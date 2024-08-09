# from ultralytics import YOLO
# yolo = YOLO('best.pt')
# def get_plates(image,classes=None):
#     if classes:
#         results = yolo(image,classes=classes, half=True)[0].boxes
#     else:
#         results = yolo(image, half=True)[0].boxes
#     results = [{
#         'class':_.cls.tolist()[0],
#         'class_name':yolo.names[_.cls.tolist()[0]],
#         'prob':_.conf.tolist()[0],
#         'xyxy':_.xyxy.tolist()[0],
#         'xyxyn':_.xyxyn.tolist()[0]
#     } for _ in results]
#     return results


from models import ComplexNN,ModelManager
model = ComplexNN()
manager = ModelManager(model)
manager.load_model('bestnormal.pt')
def get_gps(_input):
    _output = manager.predict(_input)[0]
    return _output
