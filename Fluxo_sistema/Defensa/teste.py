
import os
import re
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map
import json
from io import BytesIO
import yaml
import os,io
import requests
from database_models import ImageData,DefensasConcreto, Trip, DefensasMetal
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
from gps_predict import Geolocation



def predict(file_data):
    url = cfg["inference_defensa_trt"]["url"]
    files = {"file": ("image.jpg", file_data, "image/jpeg")}
    error_data = ""
    for i in range(10):  # Tenta 10 vezes antes de levantar um erro
        result = requests.post(url, files=files)
        if result.status_code // 100 == 2:
            try:
                # print(result.text,json.loads(result.text))
                return json.loads(result.text)
            except:
                print('ERRO na api')
                error_data += f"{result.status_code}: {result.content}\n"
        else:
            error_data += f"{result.status_code}: {result.content}\n"
    # Substitua este erro por um logger adequado
    print("Deu erro na requisição: " + error_data)


def get_image_binary(image):
    _, buffer = cv2.imencode(".jpg", image)
    image_bytes = io.BytesIO(buffer).getvalue()
    return image_bytes

def convert_pano2cube(panoname,cam):
    return re.sub(r'Panoramic_(\d+)',r'Cube_\1_cam'+str(cam),panoname)


def process_single_image(image_path):
    img = cv2.imread(image_path)
    image_binary = get_image_binary(img)
    prediction = predict(image_binary)
    return image_path, prediction


def filter_detection_with_label(detection_results_image, desired_label=0):
    boxes = detection_results_image['boxes']
    scores = detection_results_image['scores']
    labels = detection_results_image['labels']
    results = []
    for box, score, label in zip(boxes, scores, labels):
        if label == desired_label:
            results.append([label, score, box[0], box[1], box[2], box[3]])
    return results


def process_detection(image_path_list, detection_list, label=0):
    results = []
    first_detection = None
    last_detection = None
    missing_detections_image_ids = []
    
    for image_path, image_id, cam, latitude, longitude, guardrail_type in image_path_list:
        detection_result_image = filter_detection_with_label(detection_results[image_path], label)
        if len(detection_result_image) > 0:
            results.append([image_id, cam, latitude, longitude, detection_result_image]) 
            if not first_detection:
                first_detection = image_id
            last_detection = image_id
        else:
            missing_detections_image_ids.append([image_path, image_id, cam, latitude, longitude])
            
    
    missing_detections_image_ids = [
    item for item in missing_detections_image_ids
    if first_detection <= item[1] <= last_detection
    ]   
         
    return results, missing_detections_image_ids

trip_id = 1

Base = declarative_base()
with open("../config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
    

database_url = cfg['database']['url']
engine = create_engine(database_url)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
results = session.query(ImageData).filter(ImageData.trip_id == trip_id).order_by(asc(ImageData.order)).all()

folder, sentido_trip = session.query(Trip.root_folder, Trip.way).filter(Trip.trip_id == trip_id).all()[0]

#resultados_f = session.query(DefensasMetal).all()

class_dict = {0 : 'Concreto', 1 : 'Metal'}

class_names_to_label = {'Concreto' : 0, 'Metal' : 1}
id_defensas = {}

images_to_process = []

image_name_to_id = {}

for guardrail_type in ['Concreto', 'Metal']:


    for imagem in results:
        latitude = imagem.latitude
        longitude = imagem.longitude
        imagem_id = imagem.image_id

        # Cria um ponto com a latitude e longitude
        ponto = WKTElement(Point(longitude, latitude).wkt, srid=4326)

        if guardrail_type == 'Concreto':
            # Consulta para verificar se o ponto está dentro de algum polígono
            resultados = session.query(DefensasConcreto).filter(
                func.ST_Contains(DefensasConcreto.wkb_geometry, ponto),
                DefensasConcreto.sentido == 'NORTE').all()
        elif guardrail_type == 'Metal':
             resultados = session.query(DefensasMetal).filter(
                func.ST_Contains(DefensasMetal.wkb_geometry, ponto),
                DefensasMetal.sentido == 'NORTE').all()

        # Verifica o resultado
        if resultados:
            images_process_possible = []
            for resultado in resultados:
                if resultado.lado == 'DIREITO' and sentido_trip == 'N':
                    cam = 1
                elif resultado.lado == 'ESQUERDO' and sentido_trip == 'N':
                    cam = 3
                
                image_path = os.path.join(folder,'Cube', convert_pano2cube(imagem.image_name, cam))
                images_process_possible.append(image_path)
                #print(f"O ponto ({latitude}, {longitude}) está dentro da defesa com ogc_fid = {resultado.ogc_fid}, {resultado.lado}")
                id_defensa = resultado.ogc_fid
                if not id_defensa in id_defensas:
                    id_defensas[id_defensa] = []
                id_defensas[id_defensa].append([image_path, imagem_id, cam, latitude, longitude, guardrail_type])
                
            images_to_process.extend(set(images_process_possible))


detection_results = {}    

num_cpus = 20

with Pool(processes=num_cpus) as pool:
    for image_path, prediction in tqdm(
        pool.imap_unordered(process_single_image, images_to_process), total=len(images_to_process)
    ):
        detection_results[image_path] = prediction

assert len(detection_results) == len(images_to_process)


for geometry_id in tqdm(id_defensas):
    
    images_path_list = id_defensas[geometry_id]
    guardrail_type = images_path_list[0][5]
    detection_results_concrete, missing_detections_image_ids = process_detection(images_path_list, detection_results, class_names_to_label[guardrail_type])
    
    for detection in detection_results_concrete:
        latitude, longitude = detection[2], detection[3]
        for box in detection[4]:
            bbox = f"POLYGON(({box[2]} {box[3]}, {box[4]} {box[3]}, {box[4]} {box[5]}, {box[2]} {box[5]}, {box[2]} {box[3]}))"
            print(detection)
            print(bbox)
            _ = DefensasDatabase(
                    class_value = box[0],
                    class_name = class_dict[box[0]],
                    cam = detection[1],
                    geom = f'SRID=4326;POINT({longitude} {latitude})',
                    bbox = text(f"ST_GeomFromText('SRID=4326;{bbox}')"),
                    image_id = detection[0],
                    guardrail_geometry_id = geometry_id
                )
            session.add(_)
            
    session.commit()
    
    
    
    defense_detection_score = len(detection_results_concrete) / len(images_path_list)
    
    _ = DetectionGuardrailsAverage(
        average = defense_detection_score,
        cam = images_path_list[0][2],
        type = guardrail_type,
        guardrail_geometry_id = geometry_id
    )
    session.add(_)
    session.commit()
    
    
    for element in missing_detections_image_ids:
        
        _ = MissingGuardrails(
            cam = element[2],
            image_id = element[1],
            type = guardrail_type,
            guardrail_geometry_id = geometry_id,
            geom = f'SRID=4326;POINT({element[4]} {element[3]})'
        )
        session.add(_)
        
    session.commit()
    
    
    print(geometry_id, defense_detection_score)
