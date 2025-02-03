import os
import cv2
from PIL import Image
from timm.data.transforms_factory import create_transform
import torch
import sys
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit
import numpy as np
from glob import glob
import matplotlib.pyplot as plt
from test_engine import get_engine


# Cria uma transformação para preprocessamento de imagens, incluindo redimensionamento e normalização de cores
transform = create_transform(input_size=(3, 448, 448), interpolation='bicubic', mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225), crop_pct=None)

# Cria um logger para registrar mensagens de aviso TensorRT
TRT_LOGGER = trt.Logger(trt.Logger.WARNING)

# Função para alocar memória para os buffers de entrada e saída
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

# Carrega o modelo do TensorRT
def load_engine(engine_file_path):
    with open(engine_file_path, "rb") as f, trt.Runtime(TRT_LOGGER) as runtime:
        return runtime.deserialize_cuda_engine(f.read())

def classifier(engine, context, h_input, d_input, h_output, d_output, input_image):
    stream = cuda.Stream()

    # Preprocess the image
    input_image = transform(input_image).numpy()

    # Copy input image data to CPU memory (host memory)
    np.copyto(h_input, input_image.ravel())

    # Copy input data from CPU memory to GPU memory (device memory)
    cuda.memcpy_htod_async(d_input, h_input, stream)

    # Execute inference asynchronously
    context.execute_async_v2(bindings=[int(d_input), int(d_output)], stream_handle=stream.handle)

    # Copy output data from GPU memory to CPU memory
    cuda.memcpy_dtoh_async(h_output, d_output, stream)

    # Synchronize CUDA stream to wait for inference to complete
    stream.synchronize()

    return h_output

def postprocess_3_classes(score, label):
    '''
    if label == 1:
        label = 2
    elif label == 2:
        label = 0
    elif label == 3:
        label = 1
    '''

    if label == 0:
        classificacao = "Alto"
    elif label == 1: 
        classificacao = "Baixo"
    elif label == 2:
        classificacao = "Médio"

    results = {"Score": score, "Label" : label, "Classificação" : classificacao}

    return results


def postprocess_4_classes(score, label):

    if label == 0:
        classificacao = "Sem Vegetação"
    elif label == 1:
        classificacao = "Alto"
    elif label == 2: 
        classificacao = "Baixo"
    elif label == 3:
        classificacao = "Medio"
        
    results = {"Score": score, "Label" : label, "Classificação" : classificacao}

    return results


class Model():

    def __init__(self, engine_path : str = '/workspace/api_folder/weights/model_8.6.plan', height : int = 448, width: int = 448):
         
        self.width = width

        self.height = height
        
        self.device_capability = torch.cuda.get_device_capability()
        
        self.engine_path = f'weights/model_{self.device_capability[0]}.{self.device_capability[1]}.plan'

        try:
            self.engine = load_engine(self.engine_path)
            self.h_input, self.d_input, self.h_output, self.d_output = allocate_buffers(self.engine)
        except Exception:
            print('starting building engine')
            get_engine(engine_file=self.engine_path)
            self.engine = load_engine(self.engine_path)

            self.h_input, self.d_input, self.h_output, self.d_output = allocate_buffers(self.engine)

            self.context = self.engine.create_execution_context()

            self.transform = transform

    def __call__(self, image : np.array, version = 1):

        img = image

        output = classifier(self.engine, self.context, self.h_input, self.d_input, self.h_output, self.d_output, image)
    
        output_tensor = torch.tensor(output)
        softmax_output = torch.nn.functional.softmax(output_tensor, dim=0)

        label = int(np.argmax(softmax_output).cpu().numpy())
        score = float(softmax_output[label].cpu().numpy())
        
        if version == 1:
            results = postprocess_4_classes(score, label)
        else:
            results = postprocess_3_classes(score, label)

        return results
    
    
model = Model()
def get_class(image, version=1):

    results = model(image, version)

    return results

