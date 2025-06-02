import os
import re
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map
import json
from io import BytesIO
import yaml
import os,io
import requests
from Defensa.database_models import ImageData,Trip
from Defensa.database_models import GuardrailDetails
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine,asc,text
from sqlalchemy.orm import sessionmaker
import cv2
from multiprocessing import Pool, cpu_count
from Defensa.gps_predict import Geolocation
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
        largest_contour = max(contours, key=cv2.contourArea)

        rect = cv2.minAreaRect(largest_contour)
        box = cv2.boxPoints(rect)  
        box = np.intp(box)  
     
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
        height, width = imagem.shape[:2] 
        dst_points = np.array([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]], dtype="float32")
        M = cv2.getPerspectiveTransform(ordered_box, dst_points)
        warped = cv2.warpPerspective(imagem, M, (width, height))
        return warped
    return imagem

def process_single_image(image_path):
    img = cv2.imread(image_path)

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
        
                outlier = predict(get_image_binary(crop), 'inference_defensa_qualidade_crop')
        else:
            outlier = {'is_outlier' : False, 'score' : -2}
        print(box, outlier)
        outlier_data.append(outlier)
    prediction['quality'] = outlier_data
    return image_path, prediction


with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

def run(connection,folder, trip_id, trip_direction):

    Base = declarative_base()
    
        
    database_url = cfg['database']['url']
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    folder, sentido_trip = session.query(Trip.root_folder, Trip.way).filter(Trip.trip_id == trip_id).all()[0]

    class_dict = {0 : 'Concreto', 1 : 'Metal'}

    class_names_to_label = {'Concreto' : 0, 'Metal' : 1}
    id_defensas = {}

    images_to_process = []

    image_name_to_id = {}

    images_query = (
                session.query(ImageData.image_id, ImageData.image_name, ImageData.latitude, ImageData.longitude)
                .filter(ImageData.trip_id == trip_id)
                .order_by(asc(ImageData.order))
                .all()
            )
    
    images_to_process_cam1 = [(convert_pano2cube(y[1], 1), y[0], y[2], y[3], 1) for y in images_query]
    images_to_process_cam3 = [(convert_pano2cube(y[1], 3), y[0], y[2], y[3], 3) for y in images_query]
    image_data_list = images_to_process_cam1 + images_to_process_cam3

    image_data = {y[0] : (y[1], y[2], y[3], y[4]) for y in image_data_list}

    image_data_geo = {y[1] : (y[0], y[2], y[3]) for y in image_data_list}

    images_to_process = list(image_data.keys())

    images_to_process = [ os.path.join(folder,'Cube', y) for y in images_to_process][:1000]

    detection_results = {}    

    num_cpus = 20

    group_size = 20
    grouped = [images_to_process[i:i + group_size] for i in range(0, len(images_to_process), group_size)]

    for group in tqdm(grouped):
        with Pool(processes=num_cpus) as pool:
            for image_path, prediction in pool.map(process_single_image, group):
                #print(image_path)
                detection_results[image_path] = prediction
        if connection is not None:
            connection.process_data_events()
            

    print(len(detection_results), len(images_to_process))
    assert len(detection_results) == len(images_to_process)

    geo = Geolocation()

    invert_cam = {1 : 3, 3 : 1}

    for image_path in detection_results:
        filename = os.path.basename(image_path)
        detection_results_image = detection_results[image_path]
        boxes = detection_results_image['boxes']
        scores = detection_results_image['scores']
        labels = detection_results_image['labels']
        outliers = detection_results_image['quality']
        image_info = image_data[filename]
        image_id, latitude, longitude, cam = image_info[0], image_info[1], image_info[2], image_info[3]
        if (image_id - 1) in image_data_geo:
            previus_latitude, previus_longitude = image_data_geo[image_id - 1][1] , image_data_geo[image_id - 1][2]
        for box, score, label, outlier in zip(boxes, scores, labels, outliers):
            if (image_id - 1) in image_data_geo:
                if trip_direction == 'N':
                    cam_projection = cam
                else:
                    cam_projection = invert_cam[cam]
                new_latitude, new_longitude = geo.get_new_coordinate((previus_latitude,previus_longitude), (latitude, longitude),box[3],int(cam_projection))
            else: 
                new_latitude = latitude
                new_longitude = longitude
            _ = GuardrailDetails(
                    class_value = label,
                    class_name = class_dict[label],
                    score = score,
                    cam = cam,
                    geom = f'SRID=4326;POINT({new_longitude} {new_latitude})',
                    x1 = box[0],
                    y1 = box[1],
                    x2 = box[2],
                    y2 = box[3],
                    image_id = image_id,
                    outlier = outlier['is_outlier'],
                    reconstruction_error = outlier['score'],
                )
            session.add(_)
        session.commit()
        if connection is not None:
            connection.process_data_events()
        

if __name__ == '__main__':
    run(None, '', 1, 'N')
