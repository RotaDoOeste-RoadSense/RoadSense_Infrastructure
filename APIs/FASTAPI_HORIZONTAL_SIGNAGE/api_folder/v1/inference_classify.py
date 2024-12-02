from ultralytics import YOLO

model = YOLO('v1/weights/best_classify.pt')

def horizontal_classify(img):
    p = model.predict(img,verbose=False)[0]   
    id = p.probs.top1
    name = model.names[id]
    return id,name
