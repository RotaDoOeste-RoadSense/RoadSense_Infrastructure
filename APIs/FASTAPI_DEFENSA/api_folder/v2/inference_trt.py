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


def postprocess(preds, img, orig_imgs, image_path='', names=None):
        """Postprocesses predictions and returns a list of Results objects."""
        if names:
            classes = list(names.keys())

        img = np.expand_dims(img, axis=0)
       
        preds = ops.non_max_suppression(preds,
                                        0.25,
                                        0.7,
                                        agnostic=False,
                                        max_det=300,
                                        classes=classes,
                                        )
        
        results = []
        if preds[0].shape[0] > 0:
            
            preds = preds[0].cpu().numpy()
            print(preds)

            for i, pred in enumerate(preds):
                
                classe = int(pred[5])

                orig_img = orig_imgs[0] if isinstance(orig_imgs, list) else orig_imgs

                if not isinstance(orig_imgs, torch.Tensor):
                    pred[:4] = ops.scale_boxes(img.shape[2:], pred[:4], orig_img.shape)
                path = image_path
                img_path = path[i] if isinstance(path, list) else path
                if classe in classes:
                    results.append(Results(orig_img=orig_img, path=img_path, names=names, boxes=pred))
               
        return results


class Yolov8_TensorRT:
     
    def __init__(self, engine_path : str = 'v2/weights/model.plan', height : int = 1024, width: int = 1024):
         
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

    def __call__(self, image : np.array, names = None):

        img = image
        if image.shape[:2] != (self.height, self.width):
            image = cv2.resize(image, (self.height, self.width))

        # Copiar imagem de entrada para GPU
        cuda.memcpy_htod(self.input_image_gpu, image)

        # Chamar o kernel CUDA para preprocessar a imagem
        self.convertToFloatAndRavel_gpu(
            self.input_image_gpu, 
            self.output_image_gpu, 
            np.int32(self.width), 
            np.int32(self.height), 
            np.int32(self.channels), 
            block=self.block, 
            grid=self.grid
        )

        output = yolo_v8_predict(self.engine, self.context, self.h_input, self.output_image_gpu, self.h_output, self.d_output)

        print(output.shape)
        output = output.reshape(1, 6, 21504)

        boxes = torch.from_numpy(output.copy())
        detections = postprocess([boxes], self.input_image_chw, [img], names=names)
        
        return detections


yolo = Yolov8_TensorRT()
def get_defensas(image):
    names = {0: 'Concreto', 1: 'Metal'}
    results = yolo(image, names)
    if len(results) == 0:
        return results
    
    results = [{
        'class':_.boxes.cls.tolist()[0],
        'class_name':_.names[_.boxes.cls.tolist()[0]],
        'prob':_.boxes.conf.tolist()[0],
        'xyxy':_.boxes.xyxy.tolist()[0],
        'xyxyn':_.boxes.xyxyn.tolist()[0]
    } for _ in results]

    return results

