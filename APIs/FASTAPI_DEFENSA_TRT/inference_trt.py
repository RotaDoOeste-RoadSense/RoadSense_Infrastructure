import pycuda.autoinit
import pycuda.driver as cuda
from pycuda.compiler import SourceModule
import torch
import tensorrt as trt
TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
import numpy as np
from test_engine import get_engine
import cv2

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

# 将xywh转xyxy
def box_cxcywh_to_xyxy(x):
    x = torch.from_numpy(x)
    x_c, y_c, w, h = x.unbind(1)
    b = [(x_c - 0.5 * w), (y_c - 0.5 * h),
         (x_c + 0.5 * w), (y_c + 0.5 * h)]
    return torch.stack(b, dim=1)


# 将0-1映射到图像
def rescale_bboxes(out_bbox, size):
    img_w, img_h = size
    b = box_cxcywh_to_xyxy(out_bbox)
    b = b.cpu().numpy()
    b = b * np.array([img_w, img_h, img_w, img_h], dtype=np.float32)
    return b

def load_engine(engine_file_path):
    with open(engine_file_path, "rb") as f, trt.Runtime(TRT_LOGGER) as runtime:
        return runtime.deserialize_cuda_engine(f.read())

def allocate_output_buffers(engine):
    input_tensor_name = engine.get_tensor_name(0)
    output_tensor_name = engine.get_tensor_name(1)
    output_tensor_name2 = engine.get_tensor_name(2)

    h_output = cuda.pagelocked_empty(trt.volume(engine.get_tensor_shape(output_tensor_name)), dtype=np.float32)
    d_output = cuda.mem_alloc(h_output.nbytes)

    h_output2 = cuda.pagelocked_empty(trt.volume(engine.get_tensor_shape(output_tensor_name2)), dtype=np.float32)
    d_output2 = cuda.mem_alloc(h_output2.nbytes)
    return h_output, d_output, h_output2, d_output2

def allocate_image_preprocess_buffers(img):
    
    input_image_gpu = cuda.mem_alloc(img.nbytes)

    output_image_gpu = cuda.mem_alloc(img.size * np.float32().itemsize)
    
    return input_image_gpu, output_image_gpu

class DETR_TRT():
    
    def __init__(self, engine_path='weights/best_fp16.plan', fp16=False):
       
        self.engine_path = engine_path
        
        try:
            self.engine = load_engine(self.engine_path)
              #alocar memoria na gpu para saidas do modelo
            self.h_output, self.d_output, self.h_output2, self.d_output2 = allocate_output_buffers(self.engine)
        except Exception as e:
            print(e)
            get_engine(engine_file=self.engine_path)
            self.engine = load_engine(self.engine_path)
        self.context = self.engine.create_execution_context() 
        self.stream = cuda.Stream()
        self.example_image = np.zeros(shape=(2048, 2048, 3), dtype=np.uint8)
        
        # Alocar memória na GPU para preprocessamento da imagem
        self.input_image_gpu, self.output_image_gpu = allocate_image_preprocess_buffers(self.example_image)
        self.block = (256, 1, 1)
        self.width = 2048
        self.height = 2048
        self.channels = 3
        self.grid = ((self.width * self.height * self.channels + self.block[0] - 1) // self.block[0], 1, 1)
        self.convertToFloatAndRavel_gpu = mod.get_function("convertToCHWAndRavel")
        
    def _postprocess_(self, prob, boxes):
        #detection_dict = {0 : [], 1 : []}
        results = []
        for score, box in zip(prob, boxes):
            label = np.argmax(score)
            confidence = score[label]
            #box = [int(x) for x in box]
            x,y,w,h = box

            x = max([0, x])
            y = max([0, y])
            w = min([2048, w])
            h = min([2048, h])

            box = [x,y,w,h]
            #print(box)
            
            #detection_dict[label].append(box)
            results.append([label, confidence, x, y, w, h])
            
        return results
    
    def _postprocess_close(self, result):
        if len(result) > 1:
            result = sorted(result, key=lambda a: a[5], reverse=True)
            close  = result[0]
            keep = []
            others = result[1:]
            for j, element in enumerate(others):
                cy = (element[3] + element[5]) // 2
                cx = (element[2]  + element[4]) // 2
                if close[3] < cy < close[5]:
                    if element[0] != close[0]:
                        keep.append(j+1)
                    elif bbox_iou(element[2:], close[2:]) < 0.1:
                            keep.append(j+1)
            keep.append(0)
            
            result = np.array(result)
            result = result[keep]
        return result
    
    
    def _postprocess_json(self, result):
        boxes, scores, labels = [], [], []
        
        for element in result:
            labels.append(int(element[0]))
            scores.append(float(element[1]))
            boxes.append([int(y) for y in element[2:]])
            
        return {'boxes' : boxes, 'scores' : scores, 'labels' : labels}
            
            
        
    def __call__(self, img : np.array):
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        image = np.ascontiguousarray(img, dtype=np.uint8)

        cuda.memcpy_htod(self.input_image_gpu, image)
                
        # Chamar o kernel CUDA para preprocessar a imagem
        self.convertToFloatAndRavel_gpu(self.input_image_gpu, self.output_image_gpu, np.int32(self.width), np.int32(self.height), np.int32(self.channels), block=self.block, grid=self.grid)

        stream = cuda.Stream()
        self.context.execute_async_v2(bindings=[int(self.output_image_gpu), int(self.d_output), int(self.d_output2)], stream_handle=stream.handle)
        # Copy output data from GPU memory to CPU memory
        cuda.memcpy_dtoh_async(self.h_output, self.d_output, stream)
        cuda.memcpy_dtoh_async(self.h_output2, self.d_output2, stream)

        # Synchronize CUDA stream to wait for inference to complete
        stream.synchronize()
        
        output_shapes =  [(1,100,3), (1,100,4)]

        scores, boxes = self.h_output.reshape(output_shapes[0]), self.h_output2.reshape(output_shapes[1])

        prob_threshold = 0.25

        prob = torch.from_numpy(scores).softmax(-1)[0,:,:-1]
        keep = prob.max(-1).values >= prob_threshold
        # convert boxes from [0; 1] to image scales
        prob =  prob.cpu().detach().numpy()
        keep = keep.cpu().detach().numpy()

        boxes = rescale_bboxes(boxes[0, keep], img.shape[:2])
        prob = prob[keep]
        
        return prob, boxes
    
    def _predict_close(self, img : np.array):
        
        prob, boxes = self.__call__(img)
        result = self._postprocess_(prob, boxes)
        result = self._postprocess_close(result)
        result = self._postprocess_json(result)
        
        return result
        

def bbox_iou(boxA, boxB):
  # https://www.pyimagesearch.com/2016/11/07/intersection-over-union-iou-for-object-detection/
  # ^^ corrected.
    
  # Determine the (x, y)-coordinates of the intersection rectangle
  xA = max(boxA[0], boxB[0])
  yA = max(boxA[1], boxB[1])
  xB = min(boxA[2], boxB[2])
  yB = min(boxA[3], boxB[3])

  interW = xB - xA + 1
  interH = yB - yA + 1

  # Correction: reject non-overlapping boxes
  if interW <=0 or interH <=0 :
    return -1.0

  interArea = interW * interH
  boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
  boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
  iou = interArea / float(boxAArea + boxBArea - interArea)
  return iou



model = DETR_TRT()

def get_detections(image):
    results = {}
    try:
        results = model._predict_close(image)
    except Exception as e:
        print(e)
        results = {'erro_modelo' : e}
    return results



if __name__ == '__main__':

    from glob import glob
    import os
    import time
    import cv2
    import shutil
    import json

    model = DETR_TRT('weights/best11_fp16.plan')

    input_dir = '/home/rdt/Desktop/Defensa Dataset/defensa_2025_3/val/images'

    outdir = 'test_detr_best11_fp16'
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.makedirs(outdir, exist_ok=True)
            
    images = glob(input_dir + '/*.jpg')     

    average_time = []

    color_dict = {0 : (0, 0, 255), 1 : (0, 255, 0)}

    #images = ['PISTA NORTE 2_Cube_000181_cam3.jpg']
    #images = glob('*.jpg')
    
    with open('gt_val.json') as f:
        data = json.load(f)['images']
    
    data = {y['file_name'] : y['id'] for y in data}
    
    save_json = 'detr_best11_fp16.json'
    
    results_json_list = []
   
    for j, im in enumerate(images):  
        
        print(f'processando imagem {j+1} de {len(images)}')

        img = cv2.imread(im)

        height, width = img.shape[:2]

        filename = os.path.basename(im)

        filename_txt = filename.replace('.jpg', '.txt')

        start = time.time()
        result = model._predict_close(img)
        tempo = time.time() - start
        
        #print(len(result))
        
        save_path = outdir + '/' + filename_txt
        
        save_file = open(save_path, 'w')

        for element in result:
            
            label, score, x, y, w ,h = element
            cv2.rectangle(img, (int(x),int(y)), (int(w),int(h)), color_dict[label], 2)    
            save_file.write(f'{int(label)} {score} {int(x)} {int(y)} {int(w)} {int(h)}\n')  
            
            bbox = [x, y, w - x, h - y]
            bbox = [float(y) for y in bbox]
            results_json_list.append({
            "image_id" : int(data[filename]),
            "category_id" : int(label),
            "bbox" : bbox,
            "score" : float(score),
            
            })
              
                
        
        cv2.imwrite(os.path.join(outdir, filename), img)
        save_file.close()
        
        average_time.append(tempo)
        
        
    print(f'tempo medio = {np.mean(average_time[2:]) * 1000} ms')

    with open(save_json, "w") as f:
        json.dump(results_json_list, f, indent=4)
    
    del model

