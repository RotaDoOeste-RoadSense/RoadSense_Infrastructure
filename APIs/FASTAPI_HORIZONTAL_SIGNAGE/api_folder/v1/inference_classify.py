# from ultralytics import YOLO

# model = YOLO('v1/weights/best_classify.pt')

from v1.model_cls import Model

model = Model('v1/weights/horizontal_cls.onnx')


def horizontal_classify(img):
    p = model(img)[0]   
    id = p.probs.top1
    name = model.names[id]
    return id,name
