#from ultralytics import YOLO
#yolo = YOLO('best.pt')
from model import Model
yolo = Model('weights/placa.onnx')
def road_side(x):
    return 'r ' if x[0]>.5 else 'l'
def get_plates(image,classes=None):
    
    #print(classes)
    if classes:
        results = yolo(image,classes=classes)
    else:
        results = yolo(image)
        
    #print(results, type(results), len(results))
        
    if len(results) > 0:
    
        #results = results[0].boxes
        
        results = [{
            'class':_.boxes.cls.tolist()[0],
            'class_name':yolo.names[int(_.boxes.cls.tolist()[0])],
            'prob':_.boxes.conf.tolist()[0],
            'xyxy':_.boxes.xyxy.tolist()[0],
            'xyxyn':_.boxes.xyxyn.tolist()[0],
            'position':road_side(_.boxes.xywhn.tolist()[0])
        } for _ in results]
    else:
        return []

    return results

