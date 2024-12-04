import os
import re
import cv2
from tqdm.contrib.concurrent import process_map
import json
from io import BytesIO
import torch
import torchvision
import yaml
import os,io
import requests
from database_models import ImageData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine,asc
from sqlalchemy.orm import sessionmaker
def convert_pano2cube(panoname,cam):
    return re.sub(r'Panoramic_(\d+)',r'Cube_\1_cam'+str(cam),panoname)
def prepare_image(file_path):
    img = torchvision.io.read_image(file_path)
    img = torchvision.transforms.Resize((1996, 1996))(img)
    img = torch.nn.functional.pad(img, (26, 26, 26, 26), 'constant', 0).type(torch.double) / 255
    return img
def tensor_to_bytes(img_tensor):
    img_uint8 = (img_tensor * 255).byte()
    img_bytes = torchvision.io.encode_jpeg(img_uint8, quality=100)
    return img_bytes.numpy().tobytes()
def predict_defense(img_tensor):
    img_bytes = tensor_to_bytes(img_tensor)
    url = cfg['inference_defensa']['url']
    files = {"file": ("image.jpg", img_bytes, "image/jpeg")}
    error_data = ''
    for i in range(10):  # Tenta 10 vezes antes de levantar um erro
        result = requests.post(url, files=files)
        if result.status_code // 100 == 2:
            try:
                return json.loads(result.text)['response']
            except Exception as e:
                error_data += f'{result.status_code}: {result.content}\n'
        else:
            error_data += f'{result.status_code}: {result.content}\n'
    print('Deu erro na requisição: ' + error_data)

folder = "/mnt/windows_share/GPS"
trip_id = 1
trip_direction = 'N' # ou 'S'

imgs_path = os.path.join(folder,'Cube')

Base = declarative_base()
with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
database_url = cfg['database']['url']
engine = create_engine(database_url)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
results = session.query(ImageData).filter(ImageData.trip_id == trip_id).order_by(asc(ImageData.order)).all()
for cam in (1,3):
    for r in results:
        im = os.path.join(imgs_path,convert_pano2cube(r.image_name,cam))
        prepared_image = prepare_image(im)
        result = predict_defense(prepared_image)
        for box in result:
            print(im)
            print(box['cls'])
            print(box['cls_name'])
            print(box['box'])
        # break
    break