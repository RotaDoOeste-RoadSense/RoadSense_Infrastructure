from ultralytics import YOLO
model = YOLO('best.pt')

classification_dic = {0 : "Vegetação_alta", 1 : "Vegetação_baixa", 2 : 'Vegetação_media'}

def get_class(image):
    results = {}
    try:
        probs = model(image, verbose=False)[0].probs
        results = {"Score": float(probs.top1conf), "Label" : probs.top1, "Classificação" : classification_dic[probs.top1]}
    except Exception as e:
        results = {'erro_modelo' : e}
        
    return results