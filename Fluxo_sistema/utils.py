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

        latitude, longitude = row['latitude'], row['longitude']

        if latitude == 0.0 or longitude == 0.0:
            continue

        ins = ImageData(
            image_name= os.path.basename(row['image_path']),
            timestamp=int(row['image_datetime'].timestamp()),
            latitude=latitude,
            longitude=longitude,
            order = index,
            trip_id = trip_id
        )
        session.add(ins)

    session.commit()
