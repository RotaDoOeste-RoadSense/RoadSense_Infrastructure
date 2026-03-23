import os
import re
from tqdm import tqdm
import json
import yaml
import requests
from Defensa.database_models import ImageData, Trip, GuardrailDetails
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
import cv2
from multiprocessing import Pool
from Defensa.gps_predict import Geolocation
import numpy as np
import io

# Importa APENAS cache de imagens
from redis_cache_utils import cache_image

from multiprocessing import Pool, cpu_count, Lock
global_lock = Lock()


with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)


def send_request(url_key, file_data, extra_data=None, max_retries=10):
    """Envia requisição (sem cache de resposta, só usa imagem cacheada)."""
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

    print("Error: " + error_data)
    return error_data


def predict(file_data, url_key="inference_guardrail_detector"):
    return send_request(url_key, file_data)


def predict_quality(file_data, box, url_key="inference_guardrail_quality"):
    data = {
        "x_min": str(box[0]),
        "y_min": str(box[1]),
        "x_max": str(box[2]),
        "y_max": str(box[3]),
    }
    return send_request(url_key, file_data, extra_data=data)


def get_image_binary(image):
    if image is None or image.size == 0:
        raise ValueError("Empty image to get_image_binary")
    _, buffer = cv2.imencode(".jpg", image)
    image_bytes = buffer.tobytes()
    return image_bytes


def convert_pano2cube(panoname, cam):
    return re.sub(r'Panoramic_(\d+)', r'Cube_\1_cam' + str(cam), panoname)


def apply_mask_on_image(image, polygon):
    mask = cv2.fillPoly(np.zeros(image.shape[:2], dtype=np.uint8), pts=[np.int32(polygon)], color=(255))
    image = cv2.bitwise_and(image, image, mask=mask)
    return image, mask


def fix_perspective(imagem):
    imagem2 = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
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
            rect[0] = pts[np.argmin(s)]
            rect[2] = pts[np.argmax(s)]
            rect[1] = pts[np.argmin(diff)]
            rect[3] = pts[np.argmax(diff)]
            return rect

        ordered_box = order_points(box)
        height, width = imagem.shape[:2]
        dst_points = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype="float32")
        M = cv2.getPerspectiveTransform(ordered_box, dst_points)
        warped = cv2.warpPerspective(imagem, M, (width, height))
        return warped
    return imagem


def process_single_image(image_path):
    """
    Processa imagem usando cache APENAS para leitura do HD.
    APIs são sempre chamadas (sem cache de resposta).
    """
    # USA CACHE: Carrega imagem do Redis em vez do HD (TTL 24h)
    img_bytes = cache_image(image_path, api_name='defensa', lock=global_lock)

    # Converte bytes para numpy array para cv2
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Chama API YOLO (sempre, sem cache de resposta)
    prediction = predict(img_bytes)
    
    #print(prediction)
    # if prediction is None:
    #     return image_path, {'labels': [], 'boxes': [], 'scores': [], 'quality': []}

    outlier_data = []

    for label, box in zip(prediction['labels'], prediction['boxes']):
        if label == 1:
            # Chama API VAE (sempre, sem cache)
            outlier = predict_quality(img_bytes, box)
            if outlier is None:
                outlier = {'is_outlier': False, 'score': -1}

            if outlier.get('is_outlier', False):
                # Chama API SAM (sempre, sem cache)
                points = predict_quality(img_bytes, box, 'inference_guardrail_segmenter')
                if points and 'points' in points:
                    img2, mask = apply_mask_on_image(img.copy(), points['points'])
                    crop = img2[box[1]:box[3], box[0]:box[2], :]
                    crop = fix_perspective(crop)

                    # Chama API qualidade crop (sempre, sem cache)
                    outlier = predict(get_image_binary(crop), 'inference_guardrail_quality_crop')
                    if outlier is None:
                        outlier = {'is_outlier': False, 'score': -1}
        else:
            outlier = {'is_outlier': False, 'score': -2}

        outlier_data.append(outlier)

    prediction['quality'] = outlier_data
    return image_path, prediction


def run(connection, folder, trip_id, trip_direction):
    Base = declarative_base()
    database_url = cfg['database']['url']
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    folder, sentido_trip = session.query(Trip.root_folder, Trip.way).filter(Trip.trip_id == trip_id).all()[0]

    class_dict = {0: 'Concreto', 1: 'Metal'}

    images_query = (
        session.query(ImageData.image_id, ImageData.image_name, ImageData.latitude, ImageData.longitude)
        .filter(ImageData.trip_id == trip_id)
        .order_by(asc(ImageData.order))
        .all()
    )

    images_to_process_cam1 = [(convert_pano2cube(y[1], 1), y[0], y[2], y[3], 1) for y in images_query]
    images_to_process_cam3 = [(convert_pano2cube(y[1], 3), y[0], y[2], y[3], 3) for y in images_query]
    image_data_list = images_to_process_cam1 + images_to_process_cam3

    image_data = {y[0]: (y[1], y[2], y[3], y[4]) for y in image_data_list}
    image_data_geo = {y[1]: (y[0], y[2], y[3]) for y in image_data_list}

    images_to_process = list(image_data.keys())
    images_to_process = [os.path.join(folder, 'Cube', y) for y in images_to_process]

    detection_results = {}
    num_cpus = 20
    group_size = 20
    grouped = [images_to_process[i:i + group_size] for i in range(0, len(images_to_process), group_size)]

    for group in tqdm(grouped, desc='Defensas'):
        with Pool(processes=num_cpus) as pool:
            for image_path, prediction in pool.map(process_single_image, group):
                detection_results[image_path] = prediction
        if connection is not None:
            connection.process_data_events()

    print(f"Processadas {len(detection_results)} de {len(images_to_process)} imagens")

    geo = Geolocation()

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
            previus_latitude, previus_longitude = image_data_geo[image_id - 1][1], image_data_geo[image_id - 1][2]

        for box, score, label, outlier in zip(boxes, scores, labels, outliers):
            if (image_id - 1) in image_data_geo:
                new_latitude, new_longitude = geo.get_new_coordinate(
                    (previus_latitude, previus_longitude), (latitude, longitude), box[3], int(cam)
                )
            else:
                new_latitude = latitude
                new_longitude = longitude

            _ = GuardrailDetails(
                class_value=label,
                class_name=class_dict[label],
                score=score,
                cam=cam,
                geom=f'SRID=4326;POINT({new_longitude} {new_latitude})',
                x1=box[0],
                y1=box[1],
                x2=box[2],
                y2=box[3],
                image_id=image_id,
                outlier=outlier.get('is_outlier', False),
                reconstruction_error=outlier.get('score', -1),
            )
            session.add(_)
        session.commit()
        if connection is not None:
            connection.process_data_events()

    session.close()


if __name__ == '__main__':
    run(None, '', 1, 'N')
