import sys
import torch
import cv2
import numpy as np
from time import time
sys.path.append("..")
from segment_anything import sam_model_registry, SamPredictor, SamAutomaticMaskGenerator
#import matplotlib.pyplot as plt

sam_checkpoint = "weights/model.pth"
model_type = "vit_l"
device = "cuda"
sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
sam.to(device=device)


#predictor = SamPredictor(sam)
predictor = SamAutomaticMaskGenerator(sam)
predictor2 = SamPredictor(sam)

# auto annotation
# box
# point

def show_anns(anns):
    if len(anns) == 0:
        return
    sorted_anns = sorted(anns, key=(lambda x: x['area']), reverse=True)
    ax = plt.gca()
    ax.set_autoscale_on(False)

    img = np.ones((sorted_anns[0]['segmentation'].shape[0], sorted_anns[0]['segmentation'].shape[1], 4))
    img[:,:,3] = 0
    for ann in sorted_anns:
        m = ann['segmentation']
        color_mask = np.concatenate([np.random.random(3), [0.35]])
        img[m] = color_mask
    ax.imshow(img)

def predict_auto(image):
    points = []
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    #img = cv2.imread('6.png')
    height, width = img.shape[:2]
    masks = predictor.generate(img)

# [0, 100, 255,  180]

def predict(image, box):
    box_length = box[2] - box[0]
    box_height = box[3] - box[1]
    if box_length == 0 or box_height == 0:
        raise ValueError("Invalid Box")
    start = time()
    points = []
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    #img = cv2.imread('6.png')
    height, width = img.shape[:2]
    cx = width // 2
    cy = height // 2
    
    time_preprocessing = time() - start
    
    start = time()
    predictor2.set_image(img)
   
    masks, scores, _ = predictor2.predict(
        point_coords=None,
        point_labels=None,
        box=np.array(box),
        multimask_output=False,
    )
    
    time_inference = time() - start
    
    start = time()

    h, w = masks.shape[:2]
   
    mask_image = masks*255
    mask_image = np.uint8(mask_image).reshape(height, width)
    
    kernel = np.ones((3, 3), np.uint8) 
    mask_image = cv2.dilate(mask_image, kernel, iterations=1) 
    contours, hierarchy = cv2.findContours(mask_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    max_area = 0
    bigest_contour = None
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_area:
            max_area = area
            bigest_contour = contour

    if bigest_contour is not None:
        bigest_contour = bigest_contour.reshape(-1, 2)
        preenchida = cv2.fillPoly(img, pts=[bigest_contour], color=(255, 0, 0))
        points = [(int(y[0]), int(y[1])) for y in bigest_contour]
        
    time_postprocessing = time() - start
    
    #print({'preprocess' : time_preprocessing*1000, 'inference' : time_inference*1000, 'posprocessing' : time_postprocessing*1000})

    return {'points' : points}

