
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
import numpy as np


def send_request(url_key, file_data, extra_data=None, max_retries=10):
    url = cfg[url_key]["url"]
    files = {"file": ("image.jpg", file_data, "image/jpeg")}
    error_data = ""

    for _ in range(max_retries):
        try:
            result = requests.post(url, files=files, data=extra_data)
            if result.status_code // 100 == 2:
                return json.loads(result.text)
            else:
                error_data += f"{result.status_code}: {result.content}\n"
        except Exception as e:
            error_data += f"Exception: {str(e)}\n"

    print("Deu erro na requisição: " + error_data)
    return error_data


def predict(file_data, url_key="inference_defensa_yolo"):
    return send_request(url_key, file_data)


def predict_quality(file_data, box, url_key="inference_defensa_qualidade"):
    data = {
        "x_min": str(box[0]),
        "y_min": str(box[1]),
        "x_max": str(box[2]),
        "y_max": str(box[3]),
    }
    return send_request(url_key, file_data, extra_data=data)


def get_image_binary(image):
    if image is None or image.size == 0:
        raise ValueError("Imagem vazia passada para get_image_binary")
    _, buffer = cv2.imencode(".jpg", image)
    image_bytes = io.BytesIO(buffer).getvalue()
    return image_bytes 

def convert_pano2cube(panoname,cam):
    return re.sub(r'Panoramic_(\d+)',r'Cube_\1_cam'+str(cam),panoname)

def apply_mask_on_image(image, polygon):
    mask = cv2.fillPoly(np.zeros(image.shape[:2], dtype=np.uint8), pts=[np.int32(polygon)], color=(255))
    image = cv2.bitwise_and(image, image, mask=mask)
    return image, mask


def corrige_perspectiva_concreto(imagem):
    imagem2 = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    lamina = np.zeros_like(imagem2, dtype=np.uint8)
    limite_threshold = 10
    _, imagem_threshold = cv2.threshold(imagem2, limite_threshold, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8) 
    img = cv2.dilate(imagem_threshold, kernel, iterations=1)

    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        # Encontrar o maior contorno
        largest_contour = max(contours, key=cv2.contourArea)

        # Obter a caixa delimitadora rotacionada
        rect = cv2.minAreaRect(largest_contour)
        box = cv2.boxPoints(rect)  # Obter os 4 vértices
        box = np.intp(box)  # Converter para inteiro
        # Ordenar os pontos no formato esperado (top-left, top-right, bottom-right, bottom-left)
        def order_points(pts):
            rect = np.zeros((4, 2), dtype="float32")
            s = pts.sum(axis=1)
            diff = np.diff(pts, axis=1)
            rect[0] = pts[np.argmin(s)]  # Top-left
            rect[2] = pts[np.argmax(s)]  # Bottom-right
            rect[1] = pts[np.argmin(diff)]  # Top-right
            rect[3] = pts[np.argmax(diff)]  # Bottom-left
            return rect

        ordered_box = order_points(box)
        # Exibir os pontos
        #print("Pontos da caixa delimitadora ordenados:", ordered_box)
        height, width = imagem.shape[:2] 
        dst_points = np.array([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]], dtype="float32")
        # Obter a matriz de transformação
        M = cv2.getPerspectiveTransform(ordered_box, dst_points)
        # Aplicar a transformação na imagem original
        warped = cv2.warpPerspective(imagem, M, (width, height))
        return warped
    
    return imagem

def process_single_image(image_path):
    img = cv2.imread(image_path)
    #print(img.shape, image_path)
    image_binary = get_image_binary(img)
    prediction = predict(image_binary)
    outlier_data = []
    
    for label, box in zip(prediction['labels'], prediction['boxes']):

        if label == 1:
            outlier = predict_quality(image_binary, box)
            if outlier['is_outlier']:
                points = predict_quality(image_binary, box, 'inference_defensa_sam')
                img2, mask = apply_mask_on_image(img, points['points'])
                crop = img2[box[1] : box[3], box[0] : box[2], :]
                crop = corrige_perspectiva_concreto(crop)
                #print(box, crop.shape)
                #cv2.imwrite('crop.png', img2)
                outlier = predict(get_image_binary(crop), 'inference_defensa_qualidade_crop')
        else:
            outlier = {'is_outlier' : False, 'score' : -2}
        print(box, outlier)
        outlier_data.append(outlier)
    prediction['quality'] = outlier_data
    return image_path, prediction


def filter_detection_with_label(detection_results_image, desired_label=0):
    
    boxes = detection_results_image['boxes']
    scores = detection_results_image['scores']
    labels = detection_results_image['labels']
    outliers = detection_results_image['quality']
    results = []
    for box, score, label, outlier in zip(boxes, scores, labels, outliers):
        if label == desired_label:
            results.append([label, score, box[0], box[1], box[2], box[3], outlier['is_outlier'], outlier['score']])
    print(results)
    return results


def process_detection(image_path_list, detection_results, label=0):
    results = []
    first_detection = None
    last_detection = None
    missing_detections_image_ids = []
    print(image_path_list)
    for image_path, image_id, cam, latitude, longitude, guardrail_type in image_path_list:
        detection_result_image = filter_detection_with_label(detection_results[image_path], label)
        if len(detection_result_image) > 0:
            results.append([image_id, cam, latitude, longitude, detection_result_image]) 
            if not first_detection:
                first_detection = image_id
            last_detection = image_id
        else:
            missing_detections_image_ids.append([image_path, image_id, cam, latitude, longitude])
            
    if first_detection is not None and last_detection is not None:
        missing_detections_image_ids = [
        item for item in missing_detections_image_ids
        if first_detection <= item[1] <= last_detection
        ]   
         
    return results, missing_detections_image_ids


def encontrar_imagens_cam1_cam3(pasta_raiz):
    imagens_encontradas = []
    for root, _, files in os.walk(pasta_raiz):
        for nome_arquivo in files:
            if nome_arquivo.lower().endswith('.jpg') and ('cam1' in nome_arquivo.lower() or 'cam3' in nome_arquivo.lower()):
                caminho_completo = os.path.join(root, nome_arquivo)
                imagens_encontradas.append(caminho_completo)
    return imagens_encontradas

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

# for guardrail_type in ['Concreto', 'Metal']:


#     for imagem in tqdm(results):
#         latitude = imagem.latitude
#         longitude = imagem.longitude
#         imagem_id = imagem.image_id

#         # Cria um ponto com a latitude e longitude
#         ponto = WKTElement(Point(longitude, latitude).wkt, srid=4326)

#         if guardrail_type == 'Concreto':
#             # Consulta para verificar se o ponto está dentro de algum polígono
#             resultados = session.query(DefensasConcreto).filter(
#                 func.ST_Contains(DefensasConcreto.wkb_geometry, ponto),
#                 DefensasConcreto.sentido == 'NORTE').all()
        
#         elif guardrail_type == 'Metal':
#              resultados = session.query(DefensasMetal).filter(
#                 func.ST_Contains(DefensasMetal.wkb_geometry, ponto),
#                 DefensasMetal.sentido == 'NORTE').all()

#         # Verifica o resultado
#         if resultados:
#             images_process_possible = []
#             for resultado in resultados:
#                 if resultado.lado == 'DIREITO':
#                     cam = 1
#                 elif resultado.lado == 'ESQUERDO':
#                     cam = 3
#                 if '2022' in folder:
#                     image_path = os.path.join(folder,'Cube_real_norte', imagem.image_name+f'_cam{cam}.jpg')
#                 else:
#                     image_path = os.path.join(folder,'Cube', imagem.image_name)
#                     image_path = convert_pano2cube(image_path, cam)
#                 #print(image_path)
#                 #image_path = os.path.join(folder,'Cube', imagem.image_name)
#                 #image_path = os.path.join(folder,'Cube', imagem.image_name)
#                 #image_path = convert_pano2cube(image_path, cam)
#                 if os.path.exists(image_path):
#                     images_process_possible.append(image_path)
#                     #print(f"O ponto ({latitude}, {longitude}) está dentro da defesa com ogc_fid = {resultado.ogc_fid}, {resultado.lado}")
#                     id_defensa = f'{resultado.ogc_fid}_{guardrail_type}'
#                     if not id_defensa in id_defensas:
#                         id_defensas[id_defensa] = []
#                     id_defensas[id_defensa].append([image_path, imagem_id, cam, latitude, longitude, guardrail_type])
                
#             images_to_process.extend(set(images_process_possible))
            
#images_to_process = ['/media/rdt/hd1/old/dados/database_2022_test/Cube_real_norte/omni7_20220308_105826_64784682_Panoramic_002039_32800_019-3815_cam3.jpg']

images_to_process = encontrar_imagens_cam1_cam3(folder)[:100]
# images_to_process = list(set(images_to_process))

with open('GPS_norte_lista_completa.txt', 'w') as f:
    json.dump(images_to_process,f,  ensure_ascii=False, indent=2)


detection_results = {}    

num_cpus = 20

with Pool(processes=num_cpus) as pool:
    for image_path, prediction in tqdm(
        pool.imap_unordered(process_single_image, images_to_process), total=len(images_to_process)
    ):
        detection_results[image_path] = prediction


print(len(detection_results), len(images_to_process))
assert len(detection_results) == len(images_to_process)


# for geometry_id_and_type in tqdm(id_defensas):
#     geometry_id, guardrail_type = geometry_id_and_type.split('_')
#     images_path_list = id_defensas[geometry_id_and_type]
#     detection_results_concrete, missing_detections_image_ids = process_detection(images_path_list, detection_results, class_names_to_label[guardrail_type])
    
#     for detection in detection_results_concrete:
#         latitude, longitude = detection[2], detection[3]
#         for box in detection[4]:
#             #bbox = f"POLYGON(({box[2]} {box[3]}, {box[4]} {box[3]}, {box[4]} {box[5]}, {box[2]} {box[5]}, {box[2]} {box[3]}))"
#             #print(detection)
#             #print(bbox)
#             _ = DefensasDatabase(
#                     class_value = box[0],
#                     class_name = class_dict[box[0]],
#                     score = box[1],
#                     cam = detection[1],
#                     geom = f'SRID=4326;POINT({longitude} {latitude})',
#                     x1 = box[2],
#                     y1 = box[3],
#                     x2 = box[4],
#                     y2 = box[5],
#                     image_id = detection[0],
#                     guardrail_geometry_id = geometry_id,
#                     outlier = box[6],
#                     outlier_score = box[7],
#                 )
#             session.add(_)
            
#     session.commit()
    
    
    
#     defense_detection_score = len(detection_results_concrete) / len(images_path_list)
    
#     _ = DetectionGuardrailsAverage(
#         average = defense_detection_score,
#         cam = images_path_list[0][2],
#         type = guardrail_type,
#         guardrail_geometry_id = geometry_id
#     )
#     session.add(_)
#     session.commit()
    
    
#     for element in missing_detections_image_ids:
        
#         _ = MissingGuardrails(
#             cam = element[2],
#             image_id = element[1],
#             class_name = guardrail_type,
#             guardrail_geometry_id = geometry_id,
#             geom = f'SRID=4326;POINT({element[4]} {element[3]})'
#         )
#         session.add(_)
        
#     session.commit()
    
    
#     print(geometry_id, defense_detection_score)


for label in [0, 1]:
    geometry_id = 1
    detection_results_concrete, missing_detections_image_ids = process_detection(images_to_process, detection_results, label)
    for detection in detection_results_concrete:
        latitude, longitude = detection[2], detection[3]
        for box in detection[4]:
            #bbox = f"POLYGON(({box[2]} {box[3]}, {box[4]} {box[3]}, {box[4]} {box[5]}, {box[2]} {box[5]}, {box[2]} {box[3]}))"
            #print(detection)
            #print(bbox)
            _ = DefensasDatabase(
                    class_value = box[0],
                    class_name = class_dict[box[0]],
                    score = box[1],
                    cam = detection[1],
                    geom = f'SRID=4326;POINT({longitude} {latitude})',
                    x1 = box[2],
                    y1 = box[3],
                    x2 = box[4],
                    y2 = box[5],
                    image_id = detection[0],
                    guardrail_geometry_id = geometry_id,
                    outlier = box[6],
                    outlier_score = box[7],
                )
            session.add(_)
    session.commit()
    