from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, asc
import yaml
import requests
import json
import re
import numpy as np
import os, io, cv2
from database_models import Trip, ImageData, Area, Vegetacao, Manutencao
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
from redis_cache_utils import cache_image
from time import time


Base = declarative_base()

with open("../config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg["database"]["url"]
engine = create_engine(database_url)

def get_image_binary(image):
    _, buffer = cv2.imencode(".jpg", image)
    image_bytes = io.BytesIO(buffer).getvalue()
    return image_bytes

def convert_pano2cube(imgname,cam):
    return re.sub(r'_Panoramic_(\d+)',r'_Cube_\1_cam'+cam,imgname)

def read_data(image_path):
    image = cache_image(image_path)
    if image is None :
        raise ValueError(f"Não foi possível ler a imagem {image_path}")
    return image


def predict(file_data):
    url = cfg["inference_vegetacao_cube"]["url"]
    files = {"file": ("image.jpg", file_data, "image/jpeg")}
    error_data = ""
    for i in range(10):  # Tenta 10 vezes antes de levantar um erro
        result = requests.post(url, files=files)
        if result.status_code // 100 == 2:
            try:
                # print(result.text,json.loads(result.text))
                return json.loads(result.text)
            except:
                #print('ERRO na api')
                error_data += f"{result.status_code}: {result.content}\n"
        else:
            error_data += f"{result.status_code}: {result.content}\n"


def process_image_data(input):
    image_path = input["image_path"]
    id = input["image_id"]

    start = time()
    image_left, image_right = read_data(image_path)
    tempo = time() - start
    print(f' ler a imagem demorou {tempo*1000} ms')

    prediction = predict(image_right)
    return os.path.basename(image_path), prediction, id
   

# folder = '/media/rdt/hd3/Cube/'
# image_filename = 'subindoserra_Panoramic_004438.jpg'
# image_path = folder + image_filename



# imagem_left, imagem_right = read_data(image_path)

# tasks = [{"image_path" : image_path, "image_id" : 1}]


# for j in tqdm(range(100)):
#     start = time()
#     #read_data(image_path)
#     print(process_image_data(tasks[0]))
#     tempo = time() - start
#     print(f'demorou {tempo*1000} ms')

def run(connection, trip_id):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    areas_query = session.query(
        Area.area_id, Area.start_image_id, Area.end_image_id, Area.section_id
    ).filter(ImageData.image_id == Area.start_image_id, ImageData.trip_id == trip_id).all()

    areas_query = np.array(areas_query)
    # ids_list = areas_query[:, 0]
  
    folder = session.query(Trip.root_folder).filter(Trip.trip_id == trip_id).all()[0][0]



    for element in tqdm(areas_query, desc='Vegetacao_predict'):
        id_area, id_ini, id_fim, id_trecho = element

        cam_left = 3
        cam_right = 1

        ids_area = [id for id in range(int(id_ini), int(id_fim) + 1)]
        images_query = (
            session.query(ImageData.image_id, ImageData.image_name)
            .filter(ImageData.trip_id == trip_id, ImageData.image_id.in_(ids_area))
            .order_by(asc(ImageData.order))
            .all()
        )
        images_list = []

        c = 0

        for image in images_query:
            id_image, image_name = image

            image_path = folder + "/Cube/" + image_name
            path_left = convert_pano2cube(image_path, '3')
            path_right = convert_pano2cube(image_path, '1')
          
            images_list.append([id_image, path_left])
            images_list.append([id_image, path_right])