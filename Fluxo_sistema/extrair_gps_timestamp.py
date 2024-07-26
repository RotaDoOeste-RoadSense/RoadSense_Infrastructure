import pandas as pd
import os,glob,yaml,re
import piexif
from sqlalchemy import create_engine, Column, Integer, String, Numeric,ForeignKey,DateTime,BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
Base = declarative_base()
class Trip(Base):
    __tablename__ = 'TRIPS'  
    trip_id = Column(Integer, primary_key=True, autoincrement=True)
    root_folder = Column(String(2000))
    timestamp = Column(DateTime, default=datetime.utcnow)
    images = relationship("ImageData", back_populates="trip")
class ImageData(Base):
    __tablename__ = 'IMAGE_DATA'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_imagem = Column(String(200), nullable=False)
    latitude = Column(Numeric(18, 15), nullable=False)
    longitude = Column(Numeric(18, 15), nullable=False)
    timestamp = Column(Integer, nullable=False)
    order = Column(BigInteger)
    trip_id = Column(Integer, ForeignKey('TRIPS.trip_id'))
    trip = relationship("Trip", back_populates="images")
def create_table(engine):
    Base.metadata.create_all(engine)
def insert_data(session, data, trip_id):
    for item in data:
        nome_imagem = item[0]
        lat = item[1]['latitude']
        lon = item[1]['longitude']
        timestamp = item[2]
        timestamp_int = int(datetime.strptime(timestamp, "%Y:%m:%d %H:%M:%S").timestamp())
        order = int(re.findall(r'(Cube|Panoramic)\_(\d{6})',nome_imagem)[0][1])
        new_record = ImageData(
            nome_imagem=nome_imagem,
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

def convert_gps_coordinates(gps_data):
    degrees = gps_data[0][0] / gps_data[0][1]
    minutes = gps_data[1][0] / gps_data[1][1] / 60.0
    seconds = gps_data[2][0] / gps_data[2][1] / 3600.0

    return degrees + minutes + seconds

def create_gps_list(path='/mnt/HD12TB/Cones/obj_train_data/'):
    dados = []
    for image_path in glob.glob(os.path.join(path,'*.jpg')):
        gps_info, timestamp = extract_gps_and_timestamp(image_path)
        dados.append([os.path.basename(image_path),gps_info,timestamp])
    return dados

def create_gps_table(path='/mnt/HD12TB/Cones/obj_train_data/',trip_id=0):
    Base = declarative_base()
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    database_url = cfg['database']['url']
    engine = create_engine(database_url)
    create_table(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    gps_list = create_gps_list(path)
    insert_data(session,gps_list,trip_id)
