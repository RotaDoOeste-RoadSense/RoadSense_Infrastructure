# import pycuda.autoinit
# import pycuda.driver as cuda
# from pycuda.compiler import SourceModule
import torch
# import tensorrt as trt
# TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
import numpy as np
from torch.utils.data import Dataset, DataLoader
import json
from ultralytics import YOLO
import cv2


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


model = YOLO('weights/train16.pt')

model_256 = YOLO('weights/best.pt')

def postprocess_close(result):
    keep = []
    if len(result) > 1:
        result = sorted(result, key=lambda a: a[5], reverse=True)
        close  = result[0]
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
    elif len(result) == 1:
        keep.append(0)
    return result, keep

def predict_yolo(model, image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result = model(image, verbose=False)[0]
    boxes = result.boxes
    labels = boxes.cls.tolist()
    scores = boxes.conf.tolist()
    boxes = boxes.xyxy.tolist()
    boxes = [tuple(map(int,y)) for y in boxes]
    labels = [int(y) for y in labels]
    
    #if len(boxes) > 0:
    #    masks = result.masks.xy
    #else: 
    print(boxes, labels, scores)
    masks = []
    results = []
    for box, label, score in zip(boxes, labels, scores):
        results.append([label, score, box[0], box[1], box[2], box[3]])
    #results, keep = postprocess_close(results)
    #if len(keep) > 0:
        # masks = np.array(masks)
        # masks = masks[keep]
    #    masks = [masks[y] for y in keep]
    return results, masks

def results_to_json(results, masks_input):
    boxes, scores, labels, masks = [], [], [], [] 
    for element, mask in zip(results, masks_input):
        label = int(element[0])
        score = float(element[1])
        box = [int(y) for y in element[2:]]
        boxes.append(box)
        scores.append(score)
        labels.append(label)
        masks.append([(int(y[0]), int(y[1])) for y in mask])
    print(len(masks))
    return {'boxes' : boxes, 'scores' : scores, 'labels' : labels, 'masks' : masks}


def results_to_json_box(results):
    boxes, scores, labels = [], [], []
    for element in results:
        label = int(element[0])
        score = float(element[1])
        box = [int(y) for y in element[2:]]
        boxes.append(box)
        scores.append(score)
        labels.append(label)
    return {'boxes' : boxes, 'scores' : scores, 'labels' : labels, 'masks' : []}


def predict_api(image):
    results = {}
    try:
        results, masks = predict_yolo(model, image)
        results = results_to_json_box(results)
    except Exception as e:
        print(e)
        results = {'erro_modelo' : e}
    return results

def predict_api_v2(image):
    results = {}
    try:
        results, masks = predict_yolo(model_256, image)
        results = results_to_json(results, masks)
    except Exception as e:
        print(e)
        results = {'erro_modelo' : e}
    return results


