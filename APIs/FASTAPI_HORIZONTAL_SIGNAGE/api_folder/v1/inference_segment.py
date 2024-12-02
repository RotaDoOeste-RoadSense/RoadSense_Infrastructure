from ultralytics import YOLO
import matplotlib.pyplot as plt
import cv2 
import numpy as np
import torch

model=YOLO('v1/weights/best_segment.pt')

def set_segment(img):
    p = model.predict(img,verbose=False)[0]
    saida = []
    for i in range(len(p.boxes.cls)):
        if torch.nonzero(p.masks.data[i]).size()[0]>2500:
            class_id = int(p.boxes.cls[i])
            class_name = model.names[class_id]
            mask = p.masks.data[i].cpu().numpy().astype(np.uint8)
            contours, hierarchy = cv2.findContours(mask,
                cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            saida.append({'id':class_id,'classname':class_name,'segment':[_[0] for _ in contours[0].tolist()]})
    return {'results':saida}

