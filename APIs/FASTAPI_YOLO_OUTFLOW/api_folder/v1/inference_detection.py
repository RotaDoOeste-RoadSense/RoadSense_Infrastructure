from ultralytics import YOLO
import matplotlib.pyplot as plt
import cv2 
import numpy as np
import torch

model=YOLO('v1/weights/best_segment.pt')

def drainage_detect_seg(img):
    results = model.predict(img, verbose=False)
    p = results[0]
    if p.masks is None:
        return {'results': []}
    saida = []
    for i in range(len(p.boxes)):
        xyxy = p.boxes.xyxy[i].cpu().tolist()
        conf = float(p.boxes.conf[i])
        cls = int(p.boxes.cls[i])
        cls_name = model.names.get(cls)
        mask_polygon_pixels = p.masks.xy[i].cpu().tolist()
        mask_polygon_normalized = p.masks.xyn[i].cpu().tolist()
        saida.append({
            'xyxy': xyxy,
            'conf': conf,
            'cls_name': cls_name,
            'mask_xy': mask_polygon_pixels,
            'mask_xyn': mask_polygon_normalized
        })
    return {'results': saida}
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

