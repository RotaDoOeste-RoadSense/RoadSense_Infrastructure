from ultralytics import RTDETR
model = RTDETR('v4/weights/best.pt')
def get_defensas(image):
    results = model.predict(image, half=True)[0].boxes
    results = ({
        'cls':int(_.cls),
        'cls_name':model.names[int(_.cls)],
        'box':_.xyxyn[0].tolist()
    } for _ in results)
    return {'response':tuple(results)}
