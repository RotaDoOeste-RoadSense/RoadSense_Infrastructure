from datetime import datetime
import os
from database_models import ImageData
import pandas as pd
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, DateTime, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
import yaml
from tqdm import tqdm
import json
from glob import glob

Base = declarative_base()

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)


def read_json(path):
    data = []
    with open(path, 'r') as f:
        data = json.load(f)
    return data


Session = sessionmaker(bind=engine)
session = Session()


def insert_image_data_from_df(trip_id, df):
    for index, row in tqdm(df.iterrows()):
        print(index, row)
        #row['CameraTime'] = row['CameraTime'].split('.')[0]
        '''
        str_time = row['CameraTime']
        if '.' in str_time:
            timestamp = int(datetime.strptime(row['CameraTime'], '%Y-%m-%dT%H:%M:%S.%f').timestamp())
        else:[x] Defensas processando tarefa 3
            timestamp = int(datetime.strptime(row['CameraTime'], '%Y-%m-%dT%H:%M:%S').timestamp())
        '''

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
        
        # if index > 1000:
        #     break
        
    print("end")
    session.commit()



def run(trip_id, csv_path):

    # Passo 1: Ler o CSV
    df = pd.read_excel(csv_path)
   
    insert_image_data_from_df(trip_id, df)


def run_json_folder(trip_id, json_folder):
    json_files = glob(json_folder + '/*.json')
    json_all = {}

    for arquive in json_files:
        json_name = os.path.splitext(os.path.basename(arquive))[0]
        data = read_json(arquive)
        inicial = data[next(iter(data))]
        final = data[next(reversed(data))]
        longitude_inicial = inicial['longitude']
        longitude_final = final['longitude']
        
        if longitude_final > longitude_inicial:
            sentido = 'Norte'
        else:
            sentido = 'Sul'

        json_all.update(data)
        
    df = pd.DataFrame.from_dict(json_all).T
    df['camera_timestamp'] = pd.to_datetime(df['camera_timestamp'], format='%Y-%m-%d %H:%M:%S.%f')
    df = df.sort_values(by='camera_timestamp')
    df = df.rename(columns={'camera_timestamp' : 'image_datetime'})
    #df.index.names = ['image_path']
    df = df.reset_index().rename(columns={'index': 'image_path'})

    # print(df.head())
    # df.to_excel('trip_teste.xlsx')
    insert_image_data_from_df(trip_id, df)
