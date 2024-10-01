from datetime import datetime
import os
from database_models import ImageData, Area
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


    area_data_list = session.query(Area).filter(Area.end_image_id <= 229096).all()

    for area_data_element in tqdm(area_data_list):

        start_image_id = area_data_element.start_image_id

        image_data = session.query(ImageData.image_name).filter(ImageData.image_id == start_image_id).first()
        filename = image_data[0]
       
        data_csv = df[df['Image_name'] == filename]
        


        id = data_csv['ID'].values

        
        if area_data_element.area_characteristics == 'lateral_direita':

            if id <= 54:
                area_data_element.area_characteristics = 'Lateral_Norte'
            else:
                area_data_element.area_characteristics = 'Lateral_Sul'

        elif area_data_element.area_characteristics == 'lateral_esquerda':
            if id <= 54:
                area_data_element.area_characteristics = 'Canteiro_Norte'
            else:
                area_data_element.area_characteristics = 'Canteiro_Sul'
        
    session.commit()

  

