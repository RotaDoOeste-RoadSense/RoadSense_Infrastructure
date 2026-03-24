import os, sys, yaml, re
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from Drenagem.database_models import Trip, ImageData, DrainageDetails
from Drenagem.gps_predict import Geolocation
from tqdm import tqdm
from geoalchemy2.elements import WKTElement
import requests

# Importa APENAS cache de imagens
from redis_cache_utils import cache_image

from multiprocessing import Pool, cpu_count, Lock
global_lock = Lock()


def commit_drainage_to_db(session, data):
    """Salva detecção de drenagem/sarjeta no banco."""
    x1, y1, x2, y2, cam, quality_value, coords, image_id, detection_type = data

    image_data = session.query(ImageData).filter(ImageData.image_id == image_id).first()
    if image_data:
        latitude, longitude = coords
        point_wkt = f'POINT({longitude} {latitude})'
        geom = WKTElement(point_wkt, srid=4326)

        new_drainage = DrainageDetails(
            detection_type=detection_type,
            x1=float(x1),
            y1=float(y1),
            x2=float(x2),
            y2=float(y2),
            cam=cam,
            quality_value=quality_value,
            geom=geom,
            image_id=image_id
        )

        session.add(new_drainage)
        return True
    else:
        print(f"Erro: Imagem com ID {image_id} não encontrada no banco de dados.")
        return False


# with open("config.yml", "r") as ymlfile:
#     cfg = yaml.safe_load(ymlfile)

from utils import load_config

cfg = load_config()

url_detection = cfg['inference_drainage_detector']['url']
url_classify = cfg['inference_drainage_quality']['url']
url_detection_sarjeta = cfg['inference_outflow_detector']['url']
url_classify_sarjeta = cfg['inference_outflow_quality']['url']
database_url = cfg['database']['url']

Base = declarative_base()
engine = create_engine(database_url)


def carrega_imagem(image_path):
    """
    Carrega imagem usando cache Redis (evita leitura do HD).
    Retorna bytes JPEG para envio à API.
    """
    # USA CACHE: Carrega do Redis em vez do HD (TTL 24h)
    return cache_image(image_path, api_name='drenagem', lock=global_lock)


def carrega_imagem_with_crop(image_path, api_response):
    """
    Carrega imagem com cache e aplica crop baseado na bbox.
    Retorna bytes JPEG do crop para classificação de qualidade.
    """
    import cv2
    import numpy as np
    import io

    # USA CACHE: Carrega bytes JPEG do Redis
    img_bytes = cache_image(image_path)

    # Converte bytes para numpy array
    nparr = np.frombuffer(img_bytes, np.uint8)
    imagem = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if imagem is None:
        raise ValueError(f"Não foi possível decodificar imagem {image_path}")

    # Aplica crop
    x1, y1, x2, y2 = list(map(int, api_response.get('xyxy', None)))
    imagem_crop = imagem[y1:y2, x1:x2]

    # Codifica crop para bytes JPEG
    _, buffer = cv2.imencode('.jpg', imagem_crop)
    imagem_bytes = buffer.tobytes()

    return imagem_bytes


def detection_using_api(image_path):
    """Detecção de drenagem (sempre chama API, sem cache de resposta)."""
    imagem_bytes = carrega_imagem(image_path)
    response = requests.post(url_detection, files={"file": imagem_bytes})
    if response.status_code // 100 == 2:
        return response.json()
    return {'results': []}


def quality_using_api(image_path, api_response):
    """Classificação de qualidade de drenagem (sempre chama API)."""
    imagem_bytes = carrega_imagem_with_crop(image_path, api_response)
    response = requests.post(url_classify, files={"file": imagem_bytes})
    if response.status_code // 100 == 2:
        return response.json()
    return {'result': 'Bom'}  # Default se falhar


def detection_using_api_outflow(image_path):
    """Detecção de sarjeta (sempre chama API, sem cache de resposta)."""
    imagem_bytes = carrega_imagem(image_path)
    response = requests.post(url_detection_sarjeta, files={"file": imagem_bytes})
    if response.status_code // 100 == 2:
        return response.json()
    return {'results': []}


def quality_using_api_outflow(image_path, api_response):
    """Classificação de qualidade de sarjeta (sempre chama API)."""
    imagem_bytes = carrega_imagem_with_crop(image_path, api_response)
    response = requests.post(url_classify_sarjeta, files={"file": imagem_bytes})
    if response.status_code // 100 == 2:
        return response.json()
    return {'result': 'Bom'}  # Default se falhar


def adjust_image_pano2cube(image_path, camera):
    """Converte nome panorâmico para Cube com câmera específica."""
    return re.sub(r'_Panoramic_(\d+)', r'_Cube_\1_cam' + camera, image_path)


def run(connection, folder, trip_id, *_):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    results = session.query(ImageData).filter(ImageData.trip_id == trip_id).order_by(asc(ImageData.order)).all()

    geo = Geolocation()
    previous_result = None

    group_size = 20
    grouped = [results[i:i + group_size] for i in range(0, len(results), group_size)]
    salvar_depois = []

    for group in tqdm(grouped, desc='Drenagem'):
        detections_in_group = []

        for result in group:
            if not previous_result:
                previous_result = result
                continue

            for cam in ['1', '3']:
                image_path = os.path.join(folder, 'Cube', adjust_image_pano2cube(result.image_name, cam))

                # Chamadas às APIs (sempre executadas, imagem vem do cache)
                api_response = detection_using_api(image_path)
                api_response_outflow = detection_using_api_outflow(image_path)

                coord1 = (previous_result.latitude, previous_result.longitude)
                coord2 = (result.latitude, result.longitude)

                # Processa detecções de drenagem
                for response in api_response.get('results', []):
                    api_quality_response = quality_using_api(image_path, response)
                    bbox = list(map(int, response.get('xyxy', None)))
                    quality = 0 if api_quality_response.get('result') == 'Bom' else 1

                    try:
                        new_coords = geo.get_new_coordinate(coord1, coord2, bbox[3], int(cam))
                    except (ValueError, KeyError):
                        new_coords = (result.latitude, result.longitude)

                    data = bbox + [int(cam), quality, new_coords, result.image_id, 'drainage']
                    detections_in_group.append(data)

                # Processa detecções de sarjeta
                for response_outflow in api_response_outflow.get('results', []):
                    api_quality_response_outflow = quality_using_api_outflow(image_path, response_outflow)
                    bbox_outflow = list(map(int, response_outflow.get('xyxy', None)))
                    quality_outflow = 0 if api_quality_response_outflow.get('result') == 'Bom' else 1

                    try:
                        new_coords_outflow = geo.get_new_coordinate(coord1, coord2, bbox_outflow[3], int(cam))
                    except (ValueError, KeyError):
                        new_coords_outflow = (result.latitude, result.longitude)

                    data_outflow = bbox_outflow + [int(cam), quality_outflow, new_coords_outflow, result.image_id,
                                                   'outflow']
                    detections_in_group.append(data_outflow)

            previous_result = result

        salvar_depois.extend(detections_in_group)

        if connection:
            connection.process_data_events()

    # Commit em batch no final
    for data_to_commit in salvar_depois:
        commit_drainage_to_db(session, data_to_commit)

    session.commit()
    session.close()


if __name__ == '__main__':
    connection = None
    folder = "/mnt/windows_share/GPS"
    trip_id = 1
    run(connection, folder, trip_id)
