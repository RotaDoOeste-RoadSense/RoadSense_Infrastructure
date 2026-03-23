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
import re
Base = declarative_base()


with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

ins = ImageData(
            image_name= 'subindoserra_Panoramic_004828.jpg',
            timestamp=1744726716,
            latitude=-15.795537666700000,
            longitude=-55.547841166700000,
            order = 391,
            trip_id = 27
        )
        
session.add(ins)

# if index > 1000:
#     break

print("end")
session.commit()