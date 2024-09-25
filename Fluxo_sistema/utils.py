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

    # Passo 4: Inserir os dados do DataFrame no banco de dados
   
    for index, row in tqdm(df.iterrows()):
        
        #row['CameraTime'] = row['CameraTime'].split('.')[0]
        '''
        str_time = row['CameraTime']
        if '.' in str_time:
            timestamp = int(datetime.strptime(row['CameraTime'], '%Y-%m-%dT%H:%M:%S.%f').timestamp())
        else:
            timestamp = int(datetime.strptime(row['CameraTime'], '%Y-%m-%dT%H:%M:%S').timestamp())
        '''
        
        
        ins = ImageData(
            image_name= os.path.basename(row['image_path']),
            timestamp=int(row['image_datetime'].timestamp()),
            latitude=row['latitude'],
            longitude=row['longitude'],
            order = index,
            trip_id = trip_id
        )
        

        '''
        if index > 10000:
            break
    
        ins = ImageData(
            image_name= os.path.basename(row['Image_name']),
            timestamp=int(timestamp),
            latitude=row['latitude'],
            longitude=row['longitude'],
            order = index,
            trip_id = trip_id
        )
        
        '''
        session.add(ins)

    session.commit()


def mock(trip_id):

    Session = sessionmaker(bind=engine)
    session = Session()


    ins = ImageData(
            image_name= 'omni7_20220312_085628_11879652_Panoramic_019031_23784_104-4781',
            timestamp=1234,
            latitude=float('-17,2000318'),
            longitude=float('-54,7598655'),
            order = 0,
            trip_id = trip_id
        )
    session.add(ins)

    session.commit()
