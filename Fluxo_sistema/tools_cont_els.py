import torch
import timm
from PIL import Image
from PIL.ExifTags import TAGS
import cv2
import numpy as np
print("timm ver:" + str(timm.__version__))
import requests
import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger,asc, Table, MetaData, select, func
from sqlalchemy.orm import sessionmaker
import yaml

# load zoedepth model from torch hub...
torch.hub.help("intel-isl/MiDaS", "DPT_BEiT_L_384", force_reload=True)  # Triggers fresh download of MiDaS repo
repo = "isl-org/ZoeDepth"
# Zoe_N trained in NYU Depth v2 (N) for indoor scenes, but worked better than other models in the highway images....
model_zoe_n = torch.hub.load(repo, "ZoeD_N", pretrained=True)

#database config
Base = declarative_base()

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)

def predict_depth(folder, image_name):
    # Load and preprocess the input image
    input_image_path = os.path.join(folder,image_name)  # Replace with your image path
    image = cv2.imread(input_image_path)  # Read the image using OpenCV
    predicted_depth = model_zoe_n.infer_pil(image, pad_input=False) 
    return predicted_depth

def getbbox_centroid_depth(detection, predicted_depth):
    bbox = detection['xyxy']
    # Calculate the centroid of the bounding box
    x_min, y_min, x_max, y_max = bbox
    centroid_x = int((x_min + x_max) / 2)
    centroid_y = int((y_min + y_max) / 2)
    # get centroid depth
    centroid_depth = predicted_depth[centroid_x,centroid_y]
    return centroid_depth

def adjust_pos(folder, trip_id):
    # Create a metadata instance
    metadata = MetaData()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    pred_guardrail_points = Table('pred_guardrails_with_geom', metadata, autoload_with=engine)
    guardrail_details = Table('guardrail_details', metadata, autoload_with=engine)
    image_points = Table('image_data_with_geom', metadata, autoload_with=engine)

    session = Session() 

    # Query to group guardrail_details by unique_id and get associated image names
    query = (
        select(guardrail_details.c.unique_id, guardrail_details.c.pred_true, image_points.c.image_name)
        .select_from(guardrail_details.join(image_points, guardrail_details.c.image_id == image_points.c.image_id))
        .group_by(guardrail_details.c.unique_id, image_points.c.image_name)
    )

    results = session.execute(query).fetchall()

    # Process and print the results
    guardrail_images = {}
    for unique_id, image_name in results:
        if unique_id not in guardrail_images:
            guardrail_images[unique_id] = []
        guardrail_images[unique_id].append(image_name)

    for unique_id, images in guardrail_images.items():
        print(f"Guardrail {unique_id} has images: {', '.join(images)}")
        predicted_depth = predict_depth(folder,image_name)
        centr_depth = getbbox_centroid_depth(detection, predicted_depth)

    session.close()





