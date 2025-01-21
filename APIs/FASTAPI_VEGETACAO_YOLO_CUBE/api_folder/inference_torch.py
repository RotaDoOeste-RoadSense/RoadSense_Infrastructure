import pycuda.autoinit
import pycuda.driver as cuda
import numpy as np
from pycuda.compiler import SourceModule
import tensorrt as trt
#from ultralytics.yolo.utils import DEFAULT_CFG, ROOT, ops
import torch
#from ultralytics.yolo.engine.results import Results
TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
from tqdm import tqdm
#from torchvision.transforms import v2
import torchvision
from time import time
import torchvision.transforms as T

cuda.init()
device = cuda.Device(0)
cuda_driver_context = device.make_context()


transform = T.Compose([
    T.Resize(448, interpolation=T.InterpolationMode.BILINEAR, antialias=True),
    #v2.ToTensor(),
    T.Normalize(mean=[0, 0, 0], std=[1, 1, 1])
])

def preprocess_image(img):
    img = transform(img).unsqueeze(0)
    return img

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


def arcface_predict(engine, context, h_input, d_input, h_output, d_output):
    context.execute_v2(bindings=[int(d_input), int(d_output)])
    cuda.memcpy_dtoh(h_output, d_output)
    return h_output


classification_dic = {0 : "Vegetação_alta", 1 : "Vegetação_baixa", 2 : 'Vegetação_media'}

def postprocess_output(output):
    label = int(np.argmax(output))
    score = float(output[label])
    response = {
        "Score" : score, 
        "Label" : label, 
        "Classificação" : classification_dic[label]}
    return response

class Arcface_TensorRT:
     
    def __init__(self, engine_path : str = 'weights/best_fp16.plan', height : int = 448, width: int = 448):
         
        self.channels = 3
        self.width = width
        self.height = height
        self.example_image = np.zeros(shape=(self.height, self.width, 3), dtype=np.uint8)
        # Alocar memória na GPU para inferencia
        self.output_image_gpu = cuda.mem_alloc(self.example_image.size * np.float32().itemsize)
        self.engine = load_engine(engine_path)
        self.h_input, self.d_input, self.h_output, self.d_output = allocate_buffers(self.engine)
        self.context = self.engine.create_execution_context()
        self.preprocess_time = []
        self.inference_time = []
        self.postprocess_time = []

    def __call__(self, image, verbose = False):

        start_preprocessing = time()
        preprocessed_image = preprocess_image(image).cpu().numpy()
        self.preprocess_time.append(time() - start_preprocessing)
       
        start_inference = time()
        image_infer = np.ascontiguousarray(preprocessed_image, dtype=np.float32)
        cuda_driver_context.push()
        cuda.memcpy_htod(self.output_image_gpu, image_infer)
        output = arcface_predict(self.engine, self.context, self.h_input, self.output_image_gpu, self.h_output, self.d_output)
        cuda_driver_context.pop()
        self.inference_time.append(time() - start_inference)

        start_postprocessing = time()
        response = postprocess_output(output)
        self.postprocess_time.append(time() - start_postprocessing)

        if verbose:
            self.profiler()

        return response
    
    def profiler(self):
        print(f'average preprocessing time is {np.mean(self.preprocess_time[-1]) * 1000 : .3f} ms')
        print(f'average inference time is {np.mean(self.inference_time[-1]) * 1000 : .3f} ms')
        print(f'average postprocessing time is {np.mean(self.postprocess_time[-1]) * 1000 : .3f} ms')
    

model = Arcface_TensorRT()


def get_class(image):
    results = {}
    try:
        results = model(image, verbose=True)
    except Exception as e:
        results = {'erro_modelo' : e}
        
    return results

if __name__ == '__main__':

    #dataset_dir = '/home/rdt/Desktop/otimizacao_V8m_cls/Dataset24-novembro/val'
    dataset_dir = '/home/rdt/Pictures/dataset_vegetacao_cube_balanced/val'

    class_dic_folder = {'alta' : 0, 'baixa' : 1, 'media' : 2}
    from PIL import Image
    from glob import glob
    import os
    import matplotlib.pyplot as plt
    from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
    from sklearn.metrics import classification_report
    import cv2

    transforma = T.ToTensor()

    folders = glob(dataset_dir + '/*')

    class_dic_folder = {'alta' : 0, 'baixa' : 1, 'media' : 2}

    ground_truth = []
    detection_results = []

    for folder in folders:
        gt_class = class_dic_folder[os.path.basename(folder)]
        images = glob(folder + '/*.jpg')
        for image_path in tqdm(images):
            img = cv2.imread(image_path)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            img = Image.fromarray(img)
            #img = torchvision.io.read_image(image_path, torchvision.io.ImageReadMode.RGB).cuda()
            #img = Image.open(image_path)
            img = transforma(img).cuda()
            output_json = model(img)
            detection_results.append(output_json['Label'])
            ground_truth.append(gt_class)


    matrix = confusion_matrix(ground_truth, detection_results)

    disp = ConfusionMatrixDisplay(confusion_matrix=matrix,

                                display_labels=['alta', 'baixa', 'media'])
    
    text = classification_report(ground_truth, detection_results)
    print(text)
    disp.plot()

    plt.savefig('v4.png')

    cuda_driver_context.pop()

    del model



    


