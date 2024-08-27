from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
import os
import cv2
import requests
import Levenshtein #python-Levenshtein
from functools import partial
from collections import Counter
import numpy as np
from tqdm import tqdm

def fuzzy(string_a,string_b):
    return Levenshtein.ratio(str(string_a),str(string_b))
def multifuzzy(a,b_list):
    return np.mean([fuzzy(a,_) for _ in b_list])
def enclidian_distance(ponto1, ponto2):
    return np.sqrt((ponto1[0] - ponto2[0])**2 + (ponto1[1] - ponto2[1])**2)
def find_median_ocr(data):
    ocr_values = [x[1]['lower'] for x in data]
    counter = Counter(ocr_values)
    max_count = max(counter.values())
    most_common = [k for k, v in counter.items() if v == max_count]
    if len(most_common) == 1:
        return [most_common[0]]
    else:
        return most_common

Base = declarative_base()

class Trips(Base):
    __tablename__ = 'TRIPS'
    trip_id = Column(Integer, primary_key=True, autoincrement=True)
    root_folder = Column(String(2000))
    timestamp = Column(String)
class ImageData(Base):
    __tablename__ = 'IMAGE_DATA'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_imagem = Column(String(200), nullable=False)
    latitude = Column(Float(precision=15), nullable=False)
    longitude = Column(Float(precision=15), nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    order = Column(BigInteger)
    trip_id = Column(Integer, ForeignKey('TRIPS.trip_id'))
    trip = relationship('Trips', back_populates='images')
Trips.images = relationship('ImageData', order_by=ImageData.id, back_populates='trip')
class AllPlatesMatched(Base):
    __tablename__ = 'all_plates_matched'
    id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(Integer, ForeignKey('IMAGE_DATA.id'))
    image = relationship('ImageData', back_populates='plates')
ImageData.plates = relationship('AllPlatesMatched', order_by=AllPlatesMatched.id, back_populates='image')
class PlateDetails(Base):
    __tablename__ = 'plate_details'
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_value = Column(Float)
    class_name = Column(String(30))
    prob = Column(Float)
    x1 = Column(Float)
    y1 = Column(Float)
    x2 = Column(Float)
    y2 = Column(Float)
    image_id = Column(Integer, ForeignKey('all_plates_matched.id'))
    plate = relationship('AllPlatesMatched', back_populates='details')
AllPlatesMatched.details = relationship('PlateDetails', order_by=PlateDetails.id, back_populates='plate')

class PlacaKm(Base):
    __tablename__ = 'placa_km'
    id_placa_km = Column(Integer, primary_key=True, autoincrement=True)
    km = Column(Integer)
    BR = Column(String(10))
    id = Column(Integer, ForeignKey('plate_details.id'))
    plate_detail = relationship('PlateDetails')

# Carregar a configuração do arquivo config.yml
import yaml
with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)

def get_plate_details(trip_id, class_value=7):
    session = Session()
    try:
        results = session.query(
            PlateDetails,
            ImageData.nome_imagem,
            ImageData.latitude,
            ImageData.longitude
        ).select_from(PlateDetails).join(AllPlatesMatched, PlateDetails.image_id == AllPlatesMatched.id).join(
            ImageData, AllPlatesMatched.image_id == ImageData.id).filter(
            PlateDetails.class_value == class_value,
            ImageData.trip_id == trip_id
        ).order_by(ImageData.order).all()
        return results
    finally:
        session.close()
def read_and_crop_image(image_path, crop_coordinates):
       image = cv2.imread(image_path)
       if image is None:
           raise ValueError(f"Image not found at {image_path}")
       x1, y1, x2, y2 = crop_coordinates
       cropped_image = image[y1:y2, x1:x2]
       _, buffer = cv2.imencode('.jpg', cropped_image)
       return buffer.tobytes()
def classify_image(api_url, image_path,image_data):
       files = {'file': (image_path, image_data, 'multipart/form-data')}
       headers = {'accept': 'application/json'}
       response = requests.post(api_url, headers=headers, files=files)
       if response.status_code == 200:
           return response.json()
       else:
           response.raise_for_status()
def get_plate_bbox(plate_details):
    x1 = 8192*5//16+3072*plate_details.x1
    x2 = 8192*5//16+3072*plate_details.x2
    y1 = 2048*plate_details.y1
    y2 = 2048*plate_details.y2
    return list(map(int,(x1,y1,x2,y2)))
def search_last_image_with_km(group,value):
    for i in range(len(group)):
        temp = group[len(group)-1-i]
        if temp[1]['lower']==value:
            return len(group)-1-i

def main(trip_id,path):
    results = get_plate_details(trip_id)
    threshold = 1e-3
    out_results = []
    temp_group = []
    for result in tqdm(results):
        plate_details, nome_imagem, latitude, longitude = result
        image_path = os.path.join(path,'Panoramic',nome_imagem)
        image = read_and_crop_image(image_path,get_plate_bbox(plate_details))
        # with open(f'/home/victor/RoadSense_Infrastructure/deletar/{os.path.basename(image_path)}','wb') as f:f.write(image)
        bbox = get_plate_bbox(plate_details)
        if plate_details.x2==1:
            continue
        h = abs(bbox[1]-bbox[3])
        w = abs(bbox[0]-bbox[2])
        if h>w:
            if w>52:
                if classify_image(cfg['api_classify_blue_plate']['url'],image_path,image):
                    if ocr_result := classify_image(cfg['api_km_ocr']['url'],image_path,image):
                        # with open(f'/home/victor/RoadSense_Infrastructure/deletar/{ocr_result['lower']}_{os.path.basename(image_path)}','wb') as f:f.write(image)
                        if len(temp_group):
                            distance = enclidian_distance((latitude,longitude),temp_group[-1][0][-2:])
                            if distance>threshold:
                                out_results.append(temp_group)
                                temp_group = list()
                        temp_group.append((result,ocr_result))
    out_results.append(temp_group)
    ____ = []
    for i,result in tqdm(enumerate(out_results)):
        median = find_median_ocr(result)
        if len(median)>1:
            buffer = [_ for _ in ____[-5:]]
            for j in range(5):
                try:
                    buffer = buffer+find_median_ocr(out_results[i+j])
                except:pass
            mean = np.mean(list(map(float,buffer)))
            std = np.std(list(map(float,buffer)))
            passeds = (np.abs(np.array(list(map(float,median)))-mean)<std).tolist()
            median = [int(_[0]) for _ in filter(lambda v: v[1], zip(median, passeds))]
            if len(median)==1:median=int(median[0])
            else:
                fuzzy_results = [multifuzzy(_,____[-2:]+find_median_ocr(out_results[i+1])+find_median_ocr(out_results[i+2])) for _ in median]
                median = int(median[np.argmax(fuzzy_results)])
        else:
            median=int(median[0])
        ____.append(median)
    group_km = ____
    print(len(group_km),len(out_results))
    session = Session()
    try:
        for i,result in enumerate(out_results):
            temp_result = result[search_last_image_with_km(result,str(group_km[i]))]
            placa_km_entry = PlacaKm(
                    km=group_km[i],
                    BR=temp_result[1]['upper'],
                    id=temp_result[0][0].id
                )
            session.add(placa_km_entry)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
if __name__ == '__main__':
    trip_id = 2
    main(trip_id,"/mnt/BKP/Viagem3/")