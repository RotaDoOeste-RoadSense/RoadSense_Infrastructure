from ultralytics import RTDETR
model = RTDETR('weights/best.pt')
def get_defensas(image):
    results = model.predict(image, half=True)[0].boxes
    results = ({
        'cls':int(_.cls),
        'cls_name':model.names[int(_.cls)],
        'box':_.xyxyn[0].tolist()
    } for _ in results.boxes)
    return {'response':tuple(results)}
