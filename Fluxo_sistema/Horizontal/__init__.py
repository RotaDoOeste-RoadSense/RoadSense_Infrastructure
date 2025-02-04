import os
import re
import time
import cv2
from tqdm.contrib.concurrent import process_map
import json
import numpy as np
import yaml
from io import BytesIO
import tqdm
import os,io
import requests
from Horizontal.database_models import ImageData, HorizontalMarkings
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text,create_engine,asc
from sqlalchemy.orm import sessionmaker
import torch
import torch.nn.functional as F
import torchvision.transforms as T
import torchvision
Base = declarative_base()
with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
database_url = cfg['database']['url']
engine = create_engine(database_url)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
def create_row(img_id,class_id,name,polygon,score):
    polygon.append(polygon[0])
    polygon_wkt = f"POLYGON(({','.join((f'{_[0]:.1f} {_[1]:.1f}' for _ in polygon))}))"
    novo_registro = HorizontalMarkings(
        class_id=class_id,
        class_name=name,
        mask_polygon=text(f"ST_GeomFromText('{polygon_wkt}')::POLYGON"),
        quality_score=score,
        image_id=img_id
    )
    session.add(novo_registro)
    session.commit()
def convert_pano2cube(panoname):
    return re.sub(r'Panoramic_(\d+)',r'Cube_\1_cam0',panoname)
def predict_quality(tensor):
    if tensor.max() <= 1.0:
        tensor = tensor * 255.0
    tensor = tensor.byte()
    
    transform = T.ToPILImage()
    image = transform(tensor)
    
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    url = cfg['inference_horizontal_quality']['url']
    files = {"file": ("image.jpg", buffer.getvalue(), "image/jpeg")}
    error_data = ''
    for i in range(10):  # Tenta 10 vezes antes de levantar um erro
        result = requests.post(url, files=files)
        if result.status_code // 100 == 2:
            try:
                class_id,class_name = result.text[1:-1].split(',')
                return int(class_id)
            except Exception as e:
                print(e)
                error_data += f'{result.status_code}: {result.content}\n'
        else:
            error_data += f'{result.status_code}: {result.content}\n'
    print('Deu erro na requisição: ' + error_data)
def predict_masks(file_name):
    with open(file_name,'rb') as obj:
        file_data = obj.read()
    url = cfg['inference_horizontal_masks']['url']
    files = {"file": ("image.jpg", file_data, "image/jpeg")}
    error_data = ''
    for i in range(10):  # Tenta 10 vezes antes de levantar um erro
        result = requests.post(url, files=files)
        if result.status_code // 100 == 2:
            try:
                return json.loads(result.text)['results']
            except:
                error_data += f'{result.status_code}: {result.content}\n'
        else:
            error_data += f'{result.status_code}: {result.content}\n'
    print('Deu erro na requisição: ' + error_data)
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
    return 1*mask_tensor.type(torch.uint8)
def dilate_tensor(mask, kernel_size=5, iterations=1):
    pad = (kernel_size - 1) // 2
    for _ in range(iterations):
        mask = torch.nn.functional.max_pool2d(mask, kernel_size, stride=1, padding=pad)
    return mask
def process_single_image(task):
    tmp = []
    response_masks = predict_masks(os.path.join(task['path'],'Cube',task['nome_imagem']))
    img = torchvision.io.read_image(os.path.join(task['path'],'Cube',task['nome_imagem']))
    shape = img.shape[-2:]
    for m in response_masks:
        if len(m['segment'])>100:
            mask = polygon_to_mask_fillpoly(shape,m['segment'])
            area = get_area_of_segmentation_mask(mask)
            cont_int = torch.ceil(torch.log10(torch.tensor(area + 1.0)))
            kernel_size = max(1, int(2 * cont_int - 5))
            mask_dilated = dilate_tensor(mask.unsqueeze(0), kernel_size, kernel_size + 1).squeeze(0)
            p1, p2 = get_bbox(mask_dilated)
            img2 = img*mask_dilated
            img2 = img2[:,p1[0]:p2[0], p1[1]:p2[1]]
            # temporary_file = f'{int(time.time()*10000)}.png'
            # torchvision.io.write_jpeg(img2,temporary_file)
            quality_id = predict_quality(img2)
            # os.remove(temporary_file)
            tmp.append((task['img_id'],m['id'],m['classname'],m['segment'],float(quality_id)))
    return tmp
def run(connection,path,trip_id):
    results = session.query(ImageData).filter(ImageData.trip_id == trip_id).order_by(asc(ImageData.order)).all()
    tasks = [{'img_id':result.image_id,'path': path, 'nome_imagem': convert_pano2cube(result.image_name)} for result in results][:100]
    grouped = [tasks[i:i + 50] for i in range(0, len(tasks), 50)]
    for group in grouped:
        connection.process_data_events()
        adicionar = process_map(process_single_image,group,chunksize=1)
        for img in adicionar:
            for mask in img:
                try:
                    create_row(*mask)
                except Exception as e:
                    print(e)

if __name__=='__main__':
    run('/mnt/windows_share/GPS',1,'')