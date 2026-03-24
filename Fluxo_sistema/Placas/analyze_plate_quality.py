import requests
import os
import io
import re
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_models import PlateDetails, AllPlatesMatched, ImageData, Trip
from tqdm import tqdm

# Importa funções de cache do módulo utilitário
from redis_cache_utils import cache_image, cache_api_response
from multiprocessing import Pool, cpu_count, Lock
global_lock = Lock()

# with open("config.yml", "r") as ymlfile:
#     cfg = yaml.safe_load(ymlfile)
from utils import load_config

cfg = load_config()

database_url = cfg['database']['url']
engine = create_engine(database_url)
session = sessionmaker(bind=engine)()


def _get_all_plates(session, viagem_id):
    results = session.query(
        PlateDetails,
        AllPlatesMatched.image_id,
        ImageData.image_name,
        ImageData.order,
        Trip.root_folder
    ).join(
        AllPlatesMatched, AllPlatesMatched.all_plates_matched_id == PlateDetails.all_plates_matched_id
    ).join(
        ImageData, AllPlatesMatched.image_id == ImageData.image_id
    ).join(
        Trip, Trip.trip_id == viagem_id
    ).filter(
        ImageData.trip_id == viagem_id
    ).all()
    return results


def desnormalize_coordinates(xyxyn, img_width, img_height):
    x1 = int(xyxyn[0] * img_width)
    y1 = int(xyxyn[1] * img_height)
    x2 = int(xyxyn[2] * img_width)
    y2 = int(xyxyn[3] * img_height)
    return x1, y1, x2, y2


def convert_pano2cube(imgname, cam):
    return re.sub(r'_Panoramic_(\d+)', r'_Cube_\1_cam' + cam, imgname)


def make_inference_with_cache(image_path, crop):
    """
    Faz inferência de qualidade com cache Redis em dois níveis:
    1. Cache da imagem original
    2. Cache da resposta da API para cada crop específico
    """
    # Importa cv2 e numpy apenas quando necessário (cache miss)
    import cv2
    import numpy as np

    # Cria chave única baseada no path da imagem + coordenadas do crop
    params = {
        'image': image_path,
        'x1': crop[0],
        'y1': crop[1],
        'x2': crop[2],
        'y2': crop[3]
    }

    def fetch():
        # Carrega imagem com cache (TTL 24h)
        img_bytes = cache_image(image_path, api_name='placas2', lock=global_lock)

        # Converte bytes JPEG para array numpy
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError(f"Erro ao decodificar imagem: {image_path}")

        img_height, img_width = img.shape[:2]
        x1, y1, x2, y2 = desnormalize_coordinates(crop, img_width, img_height)
        cropped_image = img[y1:y2, x1:x2]

        # Codifica crop para envio
        _, image_encoded = cv2.imencode('.jpg', cropped_image)
        image_bytes_io = io.BytesIO(image_encoded)

        files = {'file': ('image.jpg', image_bytes_io, 'image/jpeg')}
        headers = {'accept': 'application/json'}

        api_url = cfg['inference_sign_classifier']['url']
        response = requests.post(api_url, headers=headers, files=files)

        if response.status_code // 100 == 2:
            return response.json()
        else:
            print(f"Erro na API qualidade: {response.status_code} - {response.content}")
            return None

    # Cache da resposta da API (chave única por imagem+crop)
    return cache_api_response('plate_quality', params, fetch)


def update_plate_status_after_inference(connection, placas):
    for im in tqdm(placas, desc='Placas_qualidade'):
        if connection:
            connection.process_data_events()

        imagem = im[2]
        imagem = os.path.join(im[4], 'Cube', convert_pano2cube(imagem, str(0)))
        xyxyn = (im[0].x1, im[0].y1, im[0].x2, im[0].y2)
        plate_details_id = im[0].plate_details_id

        # Usa função com cache
        inference_result = make_inference_with_cache(imagem, xyxyn)

        # Pula se requisição falhou
        if inference_result is None:
            continue

        new_status = 1 if inference_result.get('results') == "1" else 0
        plate_details_record = session.query(PlateDetails).filter_by(
            plate_details_id=plate_details_id
        ).first()

        if plate_details_record:
            plate_details_record.status = new_status
            session.commit()


def main(connection, trip_id):
    placas = _get_all_plates(session, trip_id)
    update_plate_status_after_inference(connection, placas)


if __name__ == '__main__':
    main(None, 4)
