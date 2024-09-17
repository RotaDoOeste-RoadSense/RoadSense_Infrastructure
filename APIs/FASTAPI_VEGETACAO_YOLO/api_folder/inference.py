from ultralytics import YOLO
model = YOLO('best.pt')

classification_dic = {0 : "Vegetação_alta", 1 : "Vegetação_baixa"}

def get_class(image):

    probs = model(image)[0].probs
    results = {"Score": float(probs.top1conf), "Label" : probs.top1, "Classificação" : classification_dic[probs.top1]}
    
    return results