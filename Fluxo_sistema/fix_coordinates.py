from datetime import datetime
import os
from database_models import ImageData
import pandas as pd
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, DateTime, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
import yaml
from tqdm import tqdm

Base = declarative_base()

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)

def run(trip_id, csv_path):

    # Passo 1: Ler o CSV
    df = pd.read_excel(csv_path)

    Session = sessionmaker(bind=engine)
    session = Session()


    image_data_list = session.query(ImageData).filter_by(trip_id=trip_id).all()

    for image_data_element in tqdm(image_data_list):
        filename = image_data_element.image_name
        data_csv = df[df['Image_name'] == filename]
        
        latitude, longitude = data_csv['latitude'], data_csv['longitude']


        image_data_element.latitude = float(latitude.values[0])
        image_data_element.longitude = float(longitude.values[0])

    session.commit()

  

