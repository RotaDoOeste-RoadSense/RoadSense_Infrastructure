import pycuda.autoinit
import pycuda.driver as cuda
import numpy as np
from pycuda.compiler import SourceModule
import tensorrt as trt
from ultralytics.yolo.utils import DEFAULT_CFG, ROOT, ops
import torch
from ultralytics.yolo.engine.results import Results
TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
import cv2
import cProfile
import pstats
from glob import glob
from torch.utils.data import Dataset, DataLoader


# Definir o Kernel CUDA
mod = SourceModule("""
__global__ void convertToCHWAndRavel(unsigned char *input, float *output, int width, int height, int channels) {
    int tid = threadIdx.x + blockIdx.x * blockDim.x;

    if (tid < width * height * channels) {
        int c = tid / (width * height);
        int idx = tid % (width * height);
        int y = idx / width;
        int x = idx % width;

        // Convertendo HWC para CHW
        output[c * width * height + y * width + x] = static_cast<float>(input[y * width * channels + x * channels + c]) / 255.0f;
    }
}
""")


def allocate_buffers(engine):
    # Obtém os nomes dos tensores
    input_tensor_name = engine.get_tensor_name(0)
    output_tensor_name = engine.get_tensor_name(1)

    # Aloca buffers de entrada e saída
    h_input = cuda.pagelocked_empty(trt.volume(engine.get_tensor_shape(input_tensor_name)), dtype=np.float32)
    h_output = cuda.pagelocked_empty(trt.volume(engine.get_tensor_shape(output_tensor_name)), dtype=np.float32)
    d_input = cuda.mem_alloc(h_input.nbytes)
    d_output = cuda.mem_alloc(h_output.nbytes)

    return h_input, d_input, h_output, d_output


def load_engine(engine_file_path):
    with open(engine_file_path, "rb") as f, trt.Runtime(TRT_LOGGER) as runtime:
        return runtime.deserialize_cuda_engine(f.read())


def yolo_v8_predict(engine, context, h_input, d_input, h_output, d_output):
    stream = cuda.Stream()

    context.execute_async_v2(bindings=[int(d_input), int(d_output)], stream_handle=stream.handle)

    # Copy output data from GPU memory to CPU memory
    cuda.memcpy_dtoh_async(h_output, d_output, stream)

    # Synchronize CUDA stream to wait for inference to complete
    stream.synchronize()

    return h_output


def postprocess(preds, img, orig_imgs, image_path=''):
        """Postprocesses predictions and returns a list of Results objects."""
        names = {0: 'Pare - R1', 1: 'De a preferência - R2', 2: 'Regulamentares geral - Rx', 3: 'Advertência geral - Ax', 4: 'Advertência retangular - Ax', 5: 'Cruz de Santo André - A-41', 6: 'Branca - Educativa', 7: 'Indicativa - Verde/Azul', 8: 'Turismo - Marrom', 9: 'Obras - Laranja', 10: 'MP - Guard Rail', 11: 'Delineador - curva', 12: 'Falsa placa', 13: 'descartar', 14: 'placa_virada'}
        img = np.expand_dims(img, axis=0)
        preds = ops.non_max_suppression(preds,
                                        0.25,
                                        0.7,
                                        agnostic=False,
                                        max_det=300,
                                        classes=None,
                                        )
        
        results = []
        for i, pred in enumerate(preds):
            orig_img = orig_imgs[i] if isinstance(orig_imgs, list) else orig_imgs
            if not isinstance(orig_imgs, torch.Tensor):
                pred[:, :4] = ops.scale_boxes(img.shape[2:], pred[:, :4], orig_img.shape)
            path = image_path
            img_path = path[i] if isinstance(path, list) else path
            results.append(Results(orig_img=orig_img, path=img_path, names=names, boxes=pred))
        return results


class Yolov8_TensorRT:
     
    def __init__(self, engine_path : str = 'triton/yolo/1/model.plan', height : int = 2048, width: int = 3072):
         
        self.channels = 3

        self.width = width

        self.height = height

        self.example_image = np.zeros(shape=(self.height, self.width, 3), dtype=np.uint8)

        # Alocar memória na GPU para preprocessamento da imagem
        self.input_image_gpu = cuda.mem_alloc(self.example_image.nbytes)
        self.output_image_gpu = cuda.mem_alloc(self.example_image.size * np.float32().itemsize)

        self.engine = load_engine(engine_path)

        self.h_input, self.d_input, self.h_output, self.d_output = allocate_buffers(self.engine)

        self.context = self.engine.create_execution_context()

        self.input_image_chw = np.transpose(self.example_image, (2, 0, 1))

        self.block = (256, 1, 1)

        self.grid = ((self.width * self.height * self.channels + self.block[0] - 1) // self.block[0], 1, 1)

        self.convertToFloatAndRavel_gpu = mod.get_function("convertToCHWAndRavel")

    def __call__(self, image : np.array):

        img = image

        if image.shape[:2] == (self.height, self.width):
            # Copiar imagem de entrada para GPU
            cuda.memcpy_htod(self.input_image_gpu, image)

            # Chamar o kernel CUDA para preprocessar a imagem
            self.convertToFloatAndRavel_gpu(self.input_image_gpu, self.output_image_gpu, np.int32(self.width), np.int32(self.height), np.int32(self.channels), block=self.block, grid=self.grid)

            output = yolo_v8_predict(self.engine, self.context, self.h_input, self.output_image_gpu, self.h_output, self.d_output)

            output = output.reshape(1, 19, 129024)

            boxes = torch.from_numpy(output.copy())

            detections = postprocess([boxes], self.input_image_chw, [img])[0]

            return detections
        

class ImageDataset(Dataset):
    """images dataset."""

    def __init__(self, root_dir):
        """
        Arguments:
            csv_file (string): Path to the csv file with annotations.
            root_dir (string): Directory with all the images.
            transform (callable, optional): Optional transform to be applied
                on a sample.
        """
        self.images = glob(root_dir + '/*.jpg')
        
    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        img_name = self.images[idx]
        image = cv2.imread(img_name)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        return img_name, image
        

def main():

    model = Yolov8_TensorRT()

    from glob import glob
    from tqdm import tqdm
    import os
    from time import time

    images_dir = 'val/images'

    #images = glob(images_dir + '/*.jpg')
    dataset_loader = torch.utils.data.DataLoader(ImageDataset(images_dir),
                                             batch_size=1, shuffle=False,
                                             num_workers=4)

    outdir = 'val_tensorrt_fp32_torch'
    os.makedirs(outdir, exist_ok=True)

    average_time = []

    for data in tqdm(dataset_loader):
       
        image_path = data[0][0]
        image = data[1][0]

        image = image.numpy()

        filename = os.path.basename(image_path)

        filename_txt = filename[:-3] + 'txt'

        #image = cv2.imread(image_path)

        start = time()
        preds = model(image)
        tempo = time() - start
        average_time.append(tempo)

        boxes = preds.boxes.xywhn.tolist()

        conf = preds.boxes.conf.tolist()

        classes = preds.boxes.cls.tolist()

        save_txt = open(outdir + '/' + filename_txt, 'w')

        for box, score, classe in zip(boxes, conf, classes):

            #print(box, score, classe)
            
            #box = [int(y) for y in box]

            #cv2.rectangle(image, box[:2], box[2:], (0, 0, 255), 2)
            str_box = ' '.join([str(y) for y in box])
            save_str = f'{int(classe)} {str_box} {score} \n'
            save_txt.write(save_str)

        save_txt.close()
        
    print(f'average processing time is {np.mean(average_time) * 1000 :.3f} ms')
            

if __name__ == '__main__':

    main()