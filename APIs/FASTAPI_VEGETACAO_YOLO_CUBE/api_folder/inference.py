import numpy as np
import torch
import cv2
from time import time
from model import Model


classification_dic = {0 : "Vegetação_alta", 1 : "Vegetação_baixa", 2 : 'Vegetação_media'}

def postprocess(output):
    label = int(output.probs.top1)
    score = float(output.probs.top1conf)
    response = {
        "Score" : score, 
        "Label" : label, 
        "Classificação" : classification_dic[label]}
    return response


yolo = Model('weights/vegetacao_cls.onnx')

def get_class(image):
    results = {}
    try:
        results = yolo(image)
        if len(results) > 0:
            results = postprocess(results)
        
    except Exception as e:
        print(e)
        results = {'erro_modelo' : e}
    return results


if __name__ == '__main__':

    dataset_dir = '/home/rdt/Pictures/dataset_vegetacao_cube_balanced/val'

    class_dic_folder = {'alta' : 0, 'baixa' : 1, 'media' : 2}
    from PIL import Image
    from glob import glob
    import os
    import matplotlib.pyplot as plt
    from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
    from sklearn.metrics import classification_report
    import cv2
    from tqdm import tqdm



    folders = glob(dataset_dir + '/*')

    class_dic_folder = {'alta' : 0, 'baixa' : 1, 'media' : 2}

    ground_truth = []
    detection_results = []

    for folder in folders:
        gt_class = class_dic_folder[os.path.basename(folder)]
        images = glob(folder + '/*.jpg')
        for image_path in tqdm(images):
            img = cv2.imread(image_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
           
            output_json = yolo(img)
            detection_results.append(output_json['Label'])
            ground_truth.append(gt_class)


    matrix = confusion_matrix(ground_truth, detection_results)

    disp = ConfusionMatrixDisplay(confusion_matrix=matrix,

                                display_labels=['alta', 'baixa', 'media'])
    
    text = classification_report(ground_truth, detection_results)
    print(text)
    
    disp.plot()

    plt.savefig('confusion_matrix.png')

    del yolo