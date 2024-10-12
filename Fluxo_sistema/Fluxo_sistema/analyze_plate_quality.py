import requests
import os
import requests
from PIL import Image
import io
import cv2
import yaml
import pandas as pd
from collections import defaultdict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_models import PlateDetails,AllPlatesMatched,ImageData
def _get_all_plates(session, viagem_id):
    results = session.query(PlateDetails,AllPlatesMatched.image_id,ImageData.image_name,ImageData.order).\
        join(AllPlatesMatched, AllPlatesMatched.all_plates_matched_id == PlateDetails.all_plates_matched_id).\
        join(ImageData, AllPlatesMatched.image_id == ImageData.image_id).\
        filter(ImageData.trip_id == viagem_id).all()
    return results
def desnormalize_coordinates(xyxyn, img_width, img_height):
    x1 = int(xyxyn[0] * img_width)
    y1 = int(xyxyn[1] * img_height)
    x2 = int(xyxyn[2] * img_width)
    y2 = int(xyxyn[3] * img_height)
    return x1, y1, x2, y2
def make_inference(image,crop):
    api_url = cfg['inference_plate_quality']['url']
    img = cv2.imread(image)
    img_height, img_width = img.shape[:2]
    x1, y1, x2, y2 = desnormalize_coordinates(crop, img_width, img_height)
    cropped_image = img[y1:y2, x1:x2]
    _, image_encoded = cv2.imencode('.jpg', cropped_image)
    image_bytes = io.BytesIO(image_encoded)
    files = {'file': ('image.jpg', image_bytes, 'image/jpeg')}
    headers = {
        'accept': 'application/json',
        'Content-Type': 'multipart/form-data'
    }
    response = requests.post(api_url, headers=headers, files=files)
    return response.json()
def update_plate_status_after_inference(placas):
    for im in placas:
        imagem = im[2]
        xyxyn = (im[0].x1, im[0].y1, im[0].x2, im[0].y2)
        plate_details_id = im[0].plate_details_id
        inference_result = make_inference(imagem, xyxyn)
        new_status = 1 if inference_result.get('results')=="1" else 0
        plate_details_record = session.query(PlateDetails).filter_by(plate_details_id=plate_details_id).first()
        if plate_details_record:
            plate_details_record.status = new_status
            session.commit()
        # print(f"Atualizado plate_details_id {plate_details_id} com status {new_status}")
with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
database_url = cfg['database']['url']
engine = create_engine(database_url)
session = sessionmaker(bind=engine)()
path = '/mnt/'
placas = _get_all_plates(session,1)
update_plate_status_after_inference(placas)