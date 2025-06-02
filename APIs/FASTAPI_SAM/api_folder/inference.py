import sys
import torch
import cv2
import numpy as np
sys.path.append("..")
from segment_anything import sam_model_registry, SamPredictor, SamAutomaticMaskGenerator
#import matplotlib.pyplot as plt

sam_checkpoint = "weights/sam_vit_l_0b3195.pth"
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

    points = []
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    #img = cv2.imread('6.png')
    height, width = img.shape[:2]
    cx = width // 2
    cy = height // 2
    predictor2.set_image(img)
   
    masks, scores, _ = predictor2.predict(
        point_coords=None,
        point_labels=None,
        box=np.array(box),
        multimask_output=False,
    )

    h, w = masks.shape[:2]
    #if len(masks.shape) == 3:
    #    plt.imshow(np.transpose(np.float32(masks), (1, 2, 0)))
    #else:
    #    plt.imshow(masks.reshape(height, width))
    #plt.figure(figsize=(20,20))
    #plt.imshow(image)
    # show_anns(masks)
    # plt.axis('off')
    # plt.savefig('original.png')
    # plt.show() 

    #color = np.array([255, 255, 255, 0.5])
    #mask_image = masks.reshape(h, w, 1) * color.reshape(1, 1, -1)
    mask_image = masks*255
    mask_image = np.uint8(mask_image).reshape(height, width)
  
    # cv2.imwrite('teste_original.png', mask_image)
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
        cv2.imwrite('teste_hull.png', preenchida)
        points = [(int(y[0]), int(y[1])) for y in bigest_contour]

    return {'points' : points}

# img = cv2.imread('6.png')
# print(predict(img))

# def bbox_iou(boxA, boxB):
#   # https://www.pyimagesearch.com/2016/11/07/intersection-over-union-iou-for-object-detection/
#   # ^^ corrected.
    
#   # Determine the (x, y)-coordinates of the intersection rectangle
#   xA = max(boxA[0], boxB[0])
#   yA = max(boxA[1], boxB[1])
#   xB = min(boxA[2], boxB[2])
#   yB = min(boxA[3], boxB[3])

#   interW = xB - xA + 1
#   interH = yB - yA + 1

#   # Correction: reject non-overlapping boxes
#   if interW <=0 or interH <=0 :
#     return -1.0

#   interArea = interW * interH
#   boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
#   boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
#   iou = interArea / float(boxAArea + boxBArea - interArea)
#   return iou


# def postprocess_close(result):
#     keep = []
#     if len(result) > 1:
#         result = sorted(result, key=lambda a: a[5], reverse=True)
#         close  = result[0]
#         others = result[1:]
#         for j, element in enumerate(others):
#             cy = (element[3] + element[5]) // 2
#             cx = (element[2]  + element[4]) // 2
#             if close[3] < cy < close[5]:
#                 if element[0] != close[0]:
#                     keep.append(j+1)
#                 elif bbox_iou(element[2:], close[2:]) < 0.1:
#                         keep.append(j+1)
#         keep.append(0)
        
#         result = np.array(result)
#         result = result[keep]
#     elif len(result) == 1:
#         keep.append(0)
#     return result, keep

# def predict_yolo(model, image):
#     image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
#     result = model(image, verbose=False)[0]
#     boxes = result.boxes
#     labels = boxes.cls.tolist()
#     scores = boxes.conf.tolist()
#     boxes = boxes.xyxy.tolist()
#     boxes = [tuple(map(int,y)) for y in boxes]
#     labels = [int(y) for y in labels]
#     if len(boxes) > 0:
#         masks = result.masks.xy
#     else: 
#         masks = []
#     results = []
#     for box, label, score in zip(boxes, labels, scores):
#         results.append([label, score, box[0], box[1], box[2], box[3]])
#     results, keep = postprocess_close(results)
#     if len(keep) > 0:
#         # masks = np.array(masks)
#         # masks = masks[keep]
#         masks = [masks[y] for y in keep]
#     return results, masks

# def results_to_json(results, masks_input):
#     boxes, scores, labels, masks = [], [], [], [] 
#     for element, mask in zip(results, masks_input):
#         label = int(element[0])
#         score = float(element[1])
#         box = [int(y) for y in element[2:]]
#         boxes.append(box)
#         scores.append(score)
#         labels.append(label)
#         masks.append([(int(y[0]), int(y[1])) for y in mask])
#     print(len(masks))
#     return {'boxes' : boxes, 'scores' : scores, 'labels' : labels, 'masks' : masks}


# def predict_api(image):
#     results = {}
#     try:
#         results, masks = predict_yolo(model, image)
#         results = results_to_json(results, masks)
#     except Exception as e:
#         print(e)
#         results = {'erro_modelo' : e}
#     return results

# def predict_api_v2(image):
#     results = {}
#     try:
#         results, masks = predict_yolo(model_256, image)
#         results = results_to_json(results, masks)
#     except Exception as e:
#         print(e)
#         results = {'erro_modelo' : e}
#     return results


