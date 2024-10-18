import torch
import timm
from PIL import Image
from PIL.ExifTags import TAGS
import cv2
import numpy as np
import requests
import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger,asc, Table, MetaData, select, func
from sqlalchemy.orm import sessionmaker
import yaml
import re # utilizar em convert_pano_cube

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

def convert_pano_cube(pano_img_name,cam):
    return re.sub(r'Panoramic_(\d{6})',f'Cube_\\1_'+cam,pano_img_name)

def predict_depth(folder, image_name):
    # Load and preprocess the input image
    input_image_path = os.path.join(folder,image_name)  # Replace with your image path
    image = cv2.imread(input_image_path)  # Read the image using OpenCV
    predicted_depth = model_zoe_n.infer_pil(image, pad_input=False) 
    return predicted_depth

def getbbox_centroid_depth(x1,y1,x2,y2,predicted_depth):
    # Get the dimensions of the predicted_depth array
    height, width = predicted_depth.shape
    # Convert the proportions to pixel coordinates
    x_min = int(x1 * width)
    y_min = int(y1 * height)
    x_max = int(x2 * width)
    y_max = int(y2 * height)

    # centroid computation
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
        select(
            guardrail_details.c.unique_id,
            guardrail_details.c.pred_true,
            guardrail_details.c.x1,
            guardrail_details.c.y1,
            guardrail_details.c.x2,
            guardrail_details.c.y2,
            guardrail_details.c.cam,
            image_points.c.image_name
        )
        .select_from(guardrail_details.join(image_points, guardrail_details.c.image_id == image_points.c.image_id))
        .where(guardrail_details.c.pred_true == 1) #only when bbox information is available....
    )

    results = session.execute(query).fetchall()

    # Dictionary to store depths for each unique_id
    depths = {}

    # Process the results
    for result in results:
        unique_id = result.unique_id
        image_name = result.image_name
        
        # Predict depth and calculate centroid depth
        predicted_depth = predict_depth(folder, convert_pano_cube(image_name,"cam"+str(result.cam)))
        centr_depth = getbbox_centroid_depth(result.x1, result.y1, result.x2, result.y2, predicted_depth)

        # Store the depth in the dictionary
        if unique_id not in depths:
            depths[unique_id] = []
        depths[unique_id].append(centr_depth)

    # Calculate and print the mean depth for each unique_id
    for unique_id, depth_list in depths.items():
        mean_depth = sum(depth_list) / len(depth_list)
        print(f"Unique ID: {unique_id}, Mean Depth: {mean_depth}")


    session.close()





