import os
import re
import json
import numpy as np
import yaml
from io import BytesIO
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map
import cv2
import requests
from Horizontal.database_models import ImageData, HorizontalMarkings
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
import torch
import torchvision.transforms as T
import torchvision

# Importa funções de cache do módulo utilitário
from redis_cache_utils import cache_image, cache_api_response

Base = declarative_base()

from multiprocessing import Pool, cpu_count, Lock
global_lock = Lock()

# with open("config.yml", "r") as ymlfile:
#     cfg = yaml.safe_load(ymlfile)

from utils import load_config

cfg = load_config()


database_url = cfg['database']['url']
engine = create_engine(database_url)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def create_row(img_id, class_id, name, polygon, score):
    polygon = [coord for point in polygon for coord in point]
    polygon_wkt = ','.join([str(y) for y in polygon])
    novo_registro = HorizontalMarkings(
        class_id=class_id,
        class_name=name,
        mask_polygon=polygon_wkt,
        quality_score=score,
        image_id=img_id
    )
    session.add(novo_registro)
    session.commit()


def convert_pano2cube(panoname):
    return re.sub(r'Panoramic_(\d+)', r'Cube_\1_cam0', panoname)


def predict_quality_with_cache(tensor, segment_hash):
    """
    Prediz qualidade de máscara com cache Redis.
    Usa hash do segmento para chave única (mesmo tensor = mesma máscara).
    """
    # Normaliza tensor para bytes
    if tensor.max() <= 1.0:
        tensor = tensor * 255.0
    tensor = tensor.byte()

    # Parâmetros únicos baseados no hash do segmento
    params = {'segment': segment_hash}

    def fetch():
        transform = T.ToPILImage()
        image = transform(tensor)

        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)

        url = cfg['inference_horizontal_classifier']['url']
        files = {"file": ("image.jpg", buffer.getvalue(), "image/jpeg")}
        error_data = ''

        for i in range(10):
            result = requests.post(url, files=files)
            if result.status_code // 100 == 2:
                try:
                    class_id, class_name = result.text[1:-1].split(',')
                    return {'class_id': int(class_id), 'class_name': class_name}
                except Exception as e:
                    print(f"Erro parse qualidade: {e}")
                    error_data += f'{result.status_code}: {result.content}\n'
            else:
                error_data += f'{result.status_code}: {result.content}\n'

        print(f'Error Requisition Horizontal Quality: {error_data}')
        return None

    response = cache_api_response('horizontal_quality', params, fetch)
    return response['class_id'] if response else None


def predict_masks_with_cache(file_path, file_data):
    """
    Prediz máscaras de marcações horizontais com cache Redis.
    Cache baseado no path da imagem.
    """
    params = {'image': file_path}

    def fetch():
        # Usa cache_image para carregar imagem (compartilhado com outros scripts)
        

        url = cfg['inference_horizontal_segmenter']['url']
        files = {"file": ("image.jpg", file_data, "image/jpeg")}
        error_data = ''

        for i in range(10):
            result = requests.post(url, files=files)
            if result.status_code // 100 == 2:
                try:
                    return json.loads(result.text)['results']
                except:
                    error_data += f'{result.status_code}: {result.content}\n'
            else:
                error_data += f'{result.status_code}: {result.content}\n'

        print(f'Error Requisition Horizontal Masks: {error_data}')
        return None

    return cache_api_response('horizontal_masks', params, fetch)


def get_area_of_segmentation_mask(segmask):
    return torch.sum(segmask).item()


def get_bbox(mask):
    coords = torch.nonzero(mask > 0)
    return torch.min(coords, dim=0).values, torch.max(coords, dim=0).values


def polygon_to_mask_fillpoly(shape, pts):
    mask_np = np.zeros(shape, dtype=np.uint8)
    pts_np = np.array([pts], dtype=np.int32)
    cv2.fillPoly(mask_np, pts_np, 1)
    mask_tensor = torch.from_numpy(mask_np).bool()
    return 1 * mask_tensor.type(torch.uint8)


def dilate_tensor(mask, kernel_size=5, iterations=1):
    pad = (kernel_size - 1) // 2
    for _ in range(iterations):
        mask = torch.nn.functional.max_pool2d(mask, kernel_size, stride=1, padding=pad)
    return mask


from PIL import Image
import io
import torch
import torchvision.transforms.functional as F


def process_single_image(task):
    tmp = []
    file_path = os.path.join(task['path'], 'Cube', task['nome_imagem'])

    image_bytes = cache_image(file_path, api_name='horizontal', lock=global_lock)
    
    # Prediz máscaras com cache
    response_masks = predict_masks_with_cache(file_path, image_bytes)
    if response_masks is None:
        return tmp

    # Carrega imagem com torchvision (sem cache adicional, pois já cacheada em predict_masks)
    #img = torchvision.io.read_image(file_path)
    #img = torchvision.io.read_image(file_data)
    
    
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = F.pil_to_tensor(img)  # retorna (C,H,W) uint8
    
    shape = img.shape[-2:]

    for m in response_masks:
        if len(m['segment']) > 100:
            mask = polygon_to_mask_fillpoly(shape, m['segment'])
            area = get_area_of_segmentation_mask(mask)
            cont_int = torch.ceil(torch.log10(torch.tensor(area + 1.0)))
            kernel_size = max(1, int(2 * cont_int - 5))
            mask_dilated = dilate_tensor(mask.unsqueeze(0), kernel_size, kernel_size + 1).squeeze(0)
            p1, p2 = get_bbox(mask_dilated)
            img2 = img * mask_dilated
            img2 = img2[:, p1[0]:p2[0], p1[1]:p2[1]]

            # Cria hash único do segmento para cache de qualidade
            segment_hash = hash(str(m['segment']))

            # Prediz qualidade com cache
            quality_id = predict_quality_with_cache(img2, segment_hash)
            if quality_id is None:
                continue

            tmp.append((task['img_id'], m['id'], m['classname'], m['segment'], float(quality_id)))

    return tmp


def run(connection, path, trip_id, *_):
    results = session.query(ImageData).filter(ImageData.trip_id == trip_id).order_by(asc(ImageData.order)).all()
    tasks = [
        {'img_id': result.image_id, 'path': path, 'nome_imagem': convert_pano2cube(result.image_name)}
        for result in results
    ]
    grouped = [tasks[i:i + 50] for i in range(0, len(tasks), 50)]

    for group in tqdm(grouped, desc='Horizontal'):
        if connection:
            connection.process_data_events()
        adicionar = process_map(process_single_image, group, chunksize=1, disable=True)
        for img in adicionar:
            for mask in img:
                try:
                    create_row(*mask)
                except Exception as e:
                    print(f"Erro ao criar row: {e}")


if __name__ == '__main__':
    run(None, '/mnt/windows_share/GPS', 1, '')
