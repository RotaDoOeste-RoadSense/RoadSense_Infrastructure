from datetime import datetime
import os
from database_models import ImageData, Trip
import pandas as pd
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, DateTime, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
import yaml
from tqdm import tqdm
import json
from glob import glob
import re
Base = declarative_base()
from sqlalchemy import asc
import shutil


def convert_pano2cube(imgname,cam):
    return re.sub(r'_Panoramic_(\d+)',r'_Cube_\1_cam'+cam,imgname)

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

trip_id = 28
results = session.query(ImageData).filter(ImageData.trip_id == trip_id).order_by(asc(ImageData.order)).all()


folder = session.query(Trip.root_folder).filter(Trip.trip_id == trip_id).all()[0][0]

print(len(results))


print(results[0].image_name, folder)

images_list = [os.path.join(folder,'Cube',convert_pano2cube(result.image_name, '0')) for result in results]

outdir = '/mnt/hd1/teste_placas_trip_'+str(trip_id)
os.makedirs(outdir, exist_ok=True)

for image in tqdm(images_list, desc='Copiando imagens'):
    shutil.copy(image, outdir)