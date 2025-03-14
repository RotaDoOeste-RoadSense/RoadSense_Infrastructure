import os
import re
from tqdm import tqdm
import json
from io import BytesIO
import yaml
import os,io
import requests
from database_models import ImageData, Trip
from database_models import MissingGuardrails, DetectionGuardrailsAverage
from database_models import DefensasDatabase
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine,asc,text
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import WKTElement
from sqlalchemy import func
from shapely.geometry import Point
import cv2
from multiprocessing import Pool, cpu_count
import shutil
import numpy as np


trip_id = 1

Base = declarative_base()
with open("../config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
    
def convert_pano2cube(panoname,cam):
    return re.sub(r'Panoramic_(\d+)',r'Cube_\1_cam'+str(cam),panoname)

database_url = cfg['database']['url']
engine = create_engine(database_url)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

Defensas_detectadas = session.query(DefensasDatabase).all()

outdir = 'Imagens_Defensas_detectadas_e_faltando'
if os.path.exists(outdir):
    shutil.rmtree(outdir)


os.makedirs(outdir, exist_ok=True)

images_folder = session.query(Trip.root_folder).filter(Trip.trip_id == trip_id).all()[0][0]
image_folder_cube = images_folder + '/Cube'


save = []

color_dict = {'Concreto' : (0, 0, 255), 'Metal' : (0 , 255, 0)}

for defensa in tqdm(Defensas_detectadas):
    image_id = defensa.image_id
    cam = defensa.cam
    id_unique_defensa = defensa.guardrail_geometry_id
    class_name = defensa.class_name
    image_filename_panoramic = session.query(ImageData.image_name).filter(ImageData.image_id == image_id).first()[0]
    image_filename_cube = convert_pano2cube(image_filename_panoramic, cam)
    x1, y1, x2, y2 = int(defensa.x1), int(defensa.y1), int(defensa.x2), int(defensa.y2)
    x1 = max(x1, 0)
    y1 = max(y1, 0)
    x2 = min(x2, 2047)
    y2 = min(y2, 2047)
    image_path_cube = os.path.join(image_folder_cube, image_filename_cube)
    save.append(image_path_cube)
    #print(image_path_cube)
    image = cv2.imread(image_path_cube)
    cv2.rectangle(image, (x1, y1), (x2, y2), color_dict[class_name], 3)
    save_folder = os.path.join(outdir, f'{class_name}_{id_unique_defensa}')
    os.makedirs(save_folder, exist_ok=True)
    save_path = os.path.join(save_folder, image_filename_cube)
    cv2.imwrite(save_path, image)
    
    
defensas_faltando = session.query(MissingGuardrails).all()
    
for defensa in tqdm(defensas_faltando):
    
    image_id = defensa.image_id
    cam = defensa.cam
    id_unique_defensa = defensa.guardrail_geometry_id
    class_name = defensa.class_name
    image_filename_panoramic = session.query(ImageData.image_name).filter(ImageData.image_id == image_id).first()[0]
    image_filename_cube = convert_pano2cube(image_filename_panoramic, cam)
    image_path_cube = os.path.join(image_folder_cube, image_filename_cube)
    save.append(image_path_cube)
    #print(image_path_cube)
    image = cv2.imread(image_path_cube)
    height, width = image.shape[:2]
    mask = np.zeros((height, width, 3), dtype=np.uint8)
    mask[:] = (0, 0, 255)  # Vermelho puro
    # Combinar a máscara com a imagem original
    alpha = 0.2  # Ajuste a transparência da máscara (0.0 - 1.0)
    image = cv2.addWeighted(image, 1 - alpha, mask, alpha, 0)
    
    save_folder = os.path.join(outdir, f'{class_name}_{id_unique_defensa}')
    os.makedirs(save_folder, exist_ok=True)
    save_path = os.path.join(save_folder, image_filename_cube)
    cv2.imwrite(save_path, image)

    
    