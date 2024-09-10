from datetime import datetime
import os
from database_models import ImageData, Area, Vegetacao, Trip
import pandas as pd
import yaml
from tqdm import tqdm
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, DateTime, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
import shutil
import pickle as pkl

Base = declarative_base()

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

areas = session.query(Area.area_id, Area.area_characteristics).all()

area_dict = {'esquerda' : [], 'direita' : []}

for element in areas:
    area_id, caracteristica = element
    if 'lateral' in caracteristica:
        area_dict['direita'].append(area_id)
    elif 'canteiro' in caracteristica:
        area_dict['esquerda'].append(area_id)


vegetation_dict = {}

trip_id = 1
folder = session.query(Trip.root_folder).filter(Trip.trip_id == trip_id).all()[0][0]

outdir = 'esquerda'
os.makedirs(outdir, exist_ok=True)

filenames_dict = {}

for lado in area_dict:

    ids_list = area_dict[lado]

    if not lado in vegetation_dict:
        vegetation_dict[lado] = {}

    if not lado in filenames_dict:
        filenames_dict[lado] = {}
    
    for id_area in tqdm(ids_list):

        vegetations_list = session.query(Vegetacao.image_file_name, Vegetacao.prediction).filter(Vegetacao.area_id == id_area)

        for filename, classe in vegetations_list:

            if not classe in vegetation_dict[lado]:
                vegetation_dict[lado][classe] = 0

            vegetation_dict[lado][classe]  += 1

            if not classe in filenames_dict[lado]:
                filenames_dict[lado][classe] = []

            filenames_dict[lado][classe].append(filename)
            '''
            if lado == 'esquerda':
                subdir = outdir + '/' + classe
                os.makedirs(subdir, exist_ok=True)

                image_path = folder +'Cube/' +filename

                save_path = subdir + '/' + filename

                shutil.copy(image_path, save_path)
            '''

print(vegetation_dict)
'''

with open('filenames_para_direita.pkl', 'wb') as f:

    pkl.dump(filenames_dict, f)
'''
            
        





