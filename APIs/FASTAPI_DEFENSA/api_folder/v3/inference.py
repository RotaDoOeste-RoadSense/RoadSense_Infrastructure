from sahi import AutoDetectionModel
from sahi.predict import get_prediction
from sahi.predict import get_sliced_prediction
from ultralytics import YOLO
import os
import shutil
import torch
from tqdm import tqdm
import numpy as np

# Define the function to convert bounding boxes to YOLO format
'''
def convert_to_yolo_format(image_width, image_height, bbox):
    x_center = (bbox[0] + bbox[2]) / 2.0 / image_width
    y_center = (bbox[1] + bbox[3]) / 2.0 / image_height
    width = (bbox[2] - bbox[0]) / image_width
    height = (bbox[3] - bbox[1]) / image_height
    return x_center, y_center, width, height
'''

# Define the function to save predictions in YOLO format
'''
def save_predictions_in_yolo_format(predictions, image_name, output_dir, image_width, image_height):
    label_file_path = os.path.join(output_dir, os.path.splitext(image_name)[0] + '.txt')
    
    with open(label_file_path, 'w') as f:
        for obj in predictions:
            #print("scooooooooooooooooooooooore:" + str(float(obj.score.value)))
            conf = obj['conf']
            class_id = obj['class']  # Assuming category.id corresponds to class label
            bbox = obj['xyxy']
            x_center, y_center, width, height = convert_to_yolo_format(image_width, image_height, bbox)
            f.write(f"{class_id} {x_center} {y_center} {width} {height} {conf}\n")
'''

def combine_predictions(predictions_both, predictions_concrete):
    """
    Combines predictions from model_both and model_concrete based on the specified rule:
    - If model_both predicts 'metal', keep the prediction.
    - Combine 'concrete' predictions from both models.

    Args:
        predictions_both (list): Predictions from model_both.
        predictions_concrete (list): Predictions from model_concrete.

    Returns:
        list: Combined list of predictions.
    """
    final_predictions = []

    # Add 'metal' predictions from `model_both` 
    # for YOLO ref: names: {0: 'Concreto', 1: 'Metal'}
    cls_names = {0: 'Concreto', 1: 'Metal'}
    pred_metal = False # metal was not predicted
    for bbox in predictions_both[0].boxes:
        prediction = {}
        cls = int(bbox.cls)
        if cls_names[cls] == 'Metal':
            pred_metal = True # a metal guardrail was predicted...
        prediction['xyxy'] = bbox.xyxy.cpu().numpy()[0]
        prediction['class'] = cls
        prediction['conf'] = float(bbox.conf)
        #print("both model pred output:")
        #print(prediction)
        final_predictions.append(prediction)
    
    for pred in predictions_concrete.object_prediction_list:
        prediction = {}
        prediction['xyxy'] = pred.bbox.to_xyxy()
        prediction['class'] = pred.category.id 
        prediction['conf'] = float(pred.score.value)
        #print("concrete model pred output:")
        #print(prediction)
        final_predictions.append(prediction)

    return final_predictions

def calculate_iou(box1, box2):
    """
    Calculate the Intersection over Union (IoU) of two bounding boxes.
    Each box is represented as a list of four numbers: [x1, y1, x2, y2].
    """
    x1, y1, x2, y2 = box1
    x1_p, y1_p, x2_p, y2_p = box2

    # Calculate the (x, y)-coordinates of the intersection rectangle
    inter_x1 = max(x1, x1_p)
    inter_y1 = max(y1, y1_p)
    inter_x2 = min(x2, x2_p)
    inter_y2 = min(y2, y2_p)

    # Compute the area of intersection rectangle
    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)

    # Compute the area of both the prediction and ground-truth rectangles
    box1_area = (x2 - x1) * (y2 - y1)
    box2_area = (x2_p - x1_p) * (y2_p - y1_p)

    # Compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the intersection area
    iou = inter_area / float(box1_area + box2_area - inter_area)
    #print("iou:" + str(iou))
    return iou

def merge_boxes(box1, box2):
    """
    Merge two bounding boxes into one.
    """
    x1 = min(box1[0], box2[0])
    y1 = min(box1[1], box2[1])
    x2 = max(box1[2], box2[2])
    y2 = max(box1[3], box2[3])
    return [x1, y1, x2, y2]

def post_process_predictions(predictions, threshold=0.5):
    """
    Post-process predictions by merging boxes with class 'Concreto' (class 0)
    if IoU >= threshold.
    """
    processed_predictions = []
    used_indices = set()

    for i, pred1 in enumerate(predictions):
        if i in used_indices or pred1['class'] != 0:
            continue

        merged_box = pred1['xyxy']
        for j, pred2 in enumerate(predictions):
            if j <= i or j in used_indices or pred2['class'] != 0:
                continue

            iou = calculate_iou(pred1['xyxy'], pred2['xyxy'])
            if iou >= threshold:
                merged_box = merge_boxes(merged_box, pred2['xyxy'])
                used_indices.add(j)

        processed_predictions.append({
            'xyxy': merged_box,
            'class': 0,  # 'Concreto'
            'conf': pred1['conf']  # You might want to adjust the confidence score
        })
        used_indices.add(i)

    # Add predictions that were not merged
    for i, pred in enumerate(predictions):
        if i not in used_indices and pred['class'] != 0:
            processed_predictions.append(pred)
    #print(processed_predictions)
    return processed_predictions

# Prepare the output directory
output_dir = "labels_pred_ensemble"
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir)


# load metal
model_both = YOLO("/mnt/internal/defensa_dir/prod_models/model_8vn_v2/weights/best.pt")

# Load the model
model_concrete = AutoDetectionModel.from_pretrained(
    model_type="yolov8",
    model_path="/mnt/internal/defensa_dir/defensa_new_scheme/concreto_pred/weights/best.pt",
    #model_path="/mnt/internal/defensa_dir/prod_models/model_8vn_v2/weights/best.pt",
    confidence_threshold=0.25,
    device='cuda:0'
)


# Move model to CUDA if available
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model_concrete.model.to(device)

# Path to the directory containing test images
image_dir = "/mnt/internal/defensa_dir/defensa_interseccao/dataset_test/images"

# Iterate over each image in the directory with progress bar
for image_name in tqdm(os.listdir(image_dir), desc="Processing Images", unit="image"):
    image_path = os.path.join(image_dir, image_name)
    # Get predictions for each image
    # Get predictions from `model_both` for both metal and concrete
    prediction_both = model_both.predict(image_path)
    # model concrete
    prediction_concrete= get_sliced_prediction(
        image=image_path,
        detection_model=model_concrete,
        slice_height=1792, # the less the height, the more fp...but the less fn...
        slice_width=768, # the less the width, the more fp...but the less fn..
        overlap_height_ratio=0.6,
        overlap_width_ratio=0.6,
        postprocess_type='NMM',
        postprocess_match_metric='IOS',
        postprocess_class_agnostic=True,
    )
    # Save predictions in YOLO format
    # Combine predictions using the function
    final_predictions = combine_predictions(prediction_both, prediction_concrete)
    # post process bboxes de concreto
    post_processed_predictions = post_process_predictions(final_predictions, threshold=1.0)

