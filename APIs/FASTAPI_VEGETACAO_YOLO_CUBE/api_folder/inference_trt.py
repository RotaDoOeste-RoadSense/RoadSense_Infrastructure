import pycuda.autoinit
import pycuda.driver as cuda
import numpy as np
from pycuda.compiler import SourceModule
import tensorrt as trt
import torch
TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
import cv2
from time import time
from test_engine import get_engine

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

classification_dic = {0 : "Vegetação_alta", 1 : "Vegetação_baixa", 2 : 'Vegetação_media'}

def postprocess(output):
    label = int(np.argmax(output))
    score = float(output[label])
    response = {
        "Score" : score, 
        "Label" : label, 
        "Classificação" : classification_dic[label]}
    return response


class Yolov8_TensorRT:
     
    def __init__(self, engine_path : str = 'weights/best_fp16.plan', height : int = 448, width: int = 448):
         
        self.channels = 3

        self.width = width

        self.height = height

        self.example_image = np.zeros(shape=(self.height, self.width, 3), dtype=np.uint8)

        # Alocar memória na GPU para preprocessamento da imagem
        self.input_image_gpu = cuda.mem_alloc(self.example_image.nbytes)
        self.output_image_gpu = cuda.mem_alloc(self.example_image.size * np.float32().itemsize)
        try:
            self.engine = load_engine(engine_path)
        except FileNotFoundError:
            get_engine()
            self.engine = load_engine(engine_path)

        self.h_input, self.d_input, self.h_output, self.d_output = allocate_buffers(self.engine)

        self.context = self.engine.create_execution_context()

        self.input_image_chw = np.transpose(self.example_image, (2, 0, 1))

        self.block = (256, 1, 1)

        self.grid = ((self.width * self.height * self.channels + self.block[0] - 1) // self.block[0], 1, 1)

        self.convertToFloatAndRavel_gpu = mod.get_function("convertToCHWAndRavel")

        self.preprocess_time = []
        self.inference_time = []
        self.postprocess_time = []

    def __call__(self, image : np.array, verbose = False):
        try:

            start_preprocessing = time()
           
            if image.shape[:2] != (448, 448):

                image = cv2.resize(image, (448, 448), interpolation=cv2.INTER_AREA)
                # = image[:, 112:560]

            image = np.ascontiguousarray(image, dtype=np.uint8)
            
            # Copiar imagem de entrada para GPU
            cuda.memcpy_htod(self.input_image_gpu, image)
           
            # Chamar o kernel CUDA para preprocessar a imagem
            self.convertToFloatAndRavel_gpu(self.input_image_gpu, self.output_image_gpu, np.int32(self.width), np.int32(self.height), np.int32(self.channels), block=self.block, grid=self.grid)

            self.preprocess_time.append(time() - start_preprocessing)

            start_inference = time()

            output = yolo_v8_predict(self.engine, self.context, self.h_input, self.output_image_gpu, self.h_output, self.d_output)
            self.inference_time.append(time() - start_inference)

            start_postprocessing = time()
            detections = postprocess(output)
            self.postprocess_time.append(time() - start_postprocessing)

            if verbose:
                self.profiler()

            return detections
        except Exception as e:
            print(e)

    def profiler(self):
        print(f'average preprocessing time is {np.mean(self.preprocess_time[1:]) * 1000 : .3f} ms')
        print(f'average inference time is {np.mean(self.inference_time[1:]) * 1000 : .3f} ms')
        print(f'average postprocessing time is {np.mean(self.postprocess_time[1:]) * 1000 : .3f} ms')

yolo = Yolov8_TensorRT()

def get_class(image):
    results = {}
    try:
        results = yolo(image, verbose=False)
    except Exception as e:
        print(e)
        results = {'erro_modelo' : e}
    return results


if __name__ == '__main__':

    dataset_dir = '/home/rdt/Pictures/dataset_vegetacao_cube_balanced/val'

    class_dic_folder = {'alta' : 0, 'baixa' : 1, 'media' : 2}
    from PIL import Image
    from glob import glob
    import os
    import matplotlib.pyplot as plt
    from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
    from sklearn.metrics import classification_report
    import cv2
    from tqdm import tqdm



    folders = glob(dataset_dir + '/*')

    class_dic_folder = {'alta' : 0, 'baixa' : 1, 'media' : 2}

    ground_truth = []
    detection_results = []

    for folder in folders:
        gt_class = class_dic_folder[os.path.basename(folder)]
        images = glob(folder + '/*.jpg')
        for image_path in tqdm(images):
            img = cv2.imread(image_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
           
            output_json = yolo(img)
            detection_results.append(output_json['Label'])
            ground_truth.append(gt_class)


    matrix = confusion_matrix(ground_truth, detection_results)

    disp = ConfusionMatrixDisplay(confusion_matrix=matrix,

                                display_labels=['alta', 'baixa', 'media'])
    
    text = classification_report(ground_truth, detection_results)
    print(text)
    
    disp.plot()

    plt.savefig('confusion_matrix.png')

    del yolo