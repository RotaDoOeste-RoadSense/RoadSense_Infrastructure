from ultralytics import YOLO
yolo = YOLO('best.pt')
def get_plates(image,classes=None):
    if classes:
        results = yolo(image,classes=classes, half=True)
    else:
        results = yolo(image, half=True)
    
    masks = results[0].masks

    results = results[0].boxes

    results = [{
        'class':_.cls.tolist()[0],
        'class_name':yolo.names[_.cls.tolist()[0]],
        'prob':_.conf.tolist()[0],
        'xyxy':_.xyxy.tolist()[0],
        'xyxyn':_.xyxyn.tolist()[0],
        'mask_xy': mask.xy[0].tolist(),
        'mask_xyn': mask.xyn[0].tolist()
    } for _, mask in zip(results, masks)]
    
    return results

