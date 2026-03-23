#from ultralytics import YOLO
#import matplotlib.pyplot as plt
import cv2 
import numpy as np
from v1.model import Model
#import torch

#model=YOLO('v1/weights/best_detector.pt')
model = Model('v1/weights/drenagem_detector.onnx')

def drainage_detect(img):
    p = model(img)
    saida = []
    if len(p) > 0:
        for i in range(len(p.boxes.cls)):
            xyxy = p.boxes.xyxy[i].cpu().tolist()
            xyxyn = p.boxes.xyxyn[i].cpu().tolist()
            conf = float(p.boxes.conf[i])
            cls = int(p.boxes.cls[i])
            cls_name = model.names.get(cls)
            saida.append({'xyxy':xyxy,'xyxyn':xyxyn,'conf':conf,'cls_name':cls_name})
            
    return {'results':saida}
    
    # saida = []
    # for i in range(len(p.boxes.cls)):
    #     if torch.nonzero(p.masks.data[i]).size()[0]>2500:
    #         class_id = int(p.boxes.cls[i])
    #         class_name = model.names[class_id]
    #         mask = p.masks.data[i].cpu().numpy().astype(np.uint8)
    #         contours, hierarchy = cv2.findContours(mask,
    #             cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    #         saida.append({'id':class_id,'classname':class_name,'segment':[_[0] for _ in contours[0].tolist()]})
    # return {'results':saida}

