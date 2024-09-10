import pandas as pd
import os,glob,yaml,re
import piexif
from sqlalchemy import create_engine, Column, Integer, String, Numeric,ForeignKey,DateTime,BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from database_models import Trip, ImageData
from datetime import datetime
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

Base = declarative_base()

def create_table(engine):
    Base.metadata.create_all(engine)

def insert_data(session, data, trip_id):
    for order,item in data.items():
        nome_imagem = item[0]
        lat = item[1]['latitude']
        lon = item[1]['longitude']
        timestamp = item[2]
        timestamp_int = int(datetime.strptime(timestamp, "%Y:%m:%d %H:%M:%S").timestamp())
        # order = int(re.findall(r'(Cube|Panoramic)\_(\d{6})',nome_imagem)[0][1])
        new_record = ImageData(
            image_name=nome_imagem,
            latitude=lat,
            longitude=lon,
            timestamp=timestamp_int,
            order=order,
            trip_id=trip_id
        )
        session.add(new_record)
    session.commit()

def extract_gps_and_timestamp(image_path):
    try:
        exif_dict = piexif.load(image_path)
        gps_info = None
        timestamp = None
        if 'GPS' in exif_dict:
            latitude_signal = {b'N':1,b'S':-1}.get(exif_dict['GPS'].get(piexif.GPSIFD.GPSLatitudeRef, None),None)
            longitude_signal = {b'E':1,b'W':-1}.get(exif_dict['GPS'].get(piexif.GPSIFD.GPSLongitudeRef, None),None)
            gps_latitude = exif_dict['GPS'].get(piexif.GPSIFD.GPSLatitude, None)
            gps_longitude = exif_dict['GPS'].get(piexif.GPSIFD.GPSLongitude, None)
            if gps_latitude and gps_longitude:
                latitude = latitude_signal*convert_gps_coordinates(gps_latitude)
                longitude = longitude_signal*convert_gps_coordinates(gps_longitude)
                gps_info = {'latitude': latitude, 'longitude': longitude}
        if 'Exif' in exif_dict:
            timestamp_str = exif_dict['Exif'].get(piexif.ExifIFD.DateTimeOriginal, None)
            if timestamp_str:
                timestamp = timestamp_str.decode('utf-8')
        return gps_info, timestamp
    except Exception as e:
        print(f"Erro ao extrair metadados da imagem: {str(e)}")
        return None, None
    
def convert_pano_cube(pano_img_name,cam):
    return re.sub(r'Panoramic_(\d{6})',f'Cube_\\1_'+cam,pano_img_name)

def convert_gps_coordinates(gps_data):
    degrees = gps_data[0][0] / gps_data[0][1]
    minutes = gps_data[1][0] / gps_data[1][1] / 60.0
    seconds = gps_data[2][0] / gps_data[2][1] / 3600.0

    return degrees + minutes + seconds




def extract_gps_timestamp_from_image(input):

    image_path = input['image_path']

    gps_info, timestamp = extract_gps_and_timestamp(image_path)

    return image_path, gps_info, timestamp


def create_gps_list(path='/mnt/HD12TB/Cones/obj_train_data/'):
    dados = []

    result_data = {}

    images_list = glob.glob(os.path.join(path,'*.jpg'))[:1000]
    tasks = [{'image_path': path} for path in images_list]
    num_cpus = cpu_count()


    with Pool(processes=num_cpus) as pool:
        for image_path, gps_info, timestamp in tqdm(pool.imap_unordered(extract_gps_timestamp_from_image, tasks), total=len(tasks)):
            result_data[image_path] = [gps_info, timestamp]
    
    for image_path in result_data:
        gps_info, timestamp = result_data[image_path]
        dados.append([os.path.basename(image_path),gps_info,timestamp])  
    '''
    for image_path in tqdm(glob.glob(os.path.join(path,'*.jpg'))):
        gps_info, timestamp = extract_gps_and_timestamp(image_path)
        dados.append([os.path.basename(image_path),gps_info,timestamp])  
    '''          
    dados = sorted(dados, key=lambda x: (int(datetime.strptime(x[2], "%Y:%m:%d %H:%M:%S").timestamp()), int(re.findall(r'(Cube|Panoramic)_(\d{6})',x[0])[0][1])))[:1000]
    return dict(enumerate(dados))

def create_gps_table(path='/mnt/HD12TB/Cones/obj_train_data/',trip_id=0):
    Base = declarative_base()
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    database_url = cfg['database']['url']
    engine = create_engine(database_url)
    # create_table(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    gps_list = create_gps_list(path)
    #print(gps_list)
    insert_data(session,gps_list,trip_id)