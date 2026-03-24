import yaml
import os
import re


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

# with open("config.yml", "r") as ymlfile:
#     cfg = yaml.safe_load(ymlfile)

def load_config(config_path="config.yml"):
    """
    Carrega o arquivo YAML e resolve variáveis de ambiente ${VAR} ou $VAR.
    """
    with open(config_path, "r") as f:
        content = f.read()
    
    # Regex para encontrar ${VAR} ou $VAR
    pattern = re.compile(r'\${(\w+)}|\$(\w+)')
    
    def replacer(match):
        var_name = match.group(1) or match.group(2)
        # Fallback para os valores padrão se não encontrar no ambiente
        defaults = {
            'DB_USER': 'myuser',
            'DB_PASS': 'mypassword',
            'DB_PORT': '1111'
        }
        return os.getenv(var_name, defaults.get(var_name, match.group(0)))

    # Substitui variáveis no texto bruto do YAML antes do parse
    resolved_content = pattern.sub(replacer, content)
    return yaml.safe_load(resolved_content)

cfg = load_config()



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


def filter_df_by_interval(df, start_image_number, final_image_number):
    fname = df['image_path'].astype(str).str.replace(r'.*[\\/]', '', regex=True)
    df['image_number'] = (
    fname.str.extract(r'(?<!_)_(\d+)(?=\.[^.]+$)', expand=False)
        )
    df['image_number'] = df['image_number'].astype('Int64')
    df = (
    df.loc[df['image_number'].between(start_image_number, final_image_number, inclusive='both')]
      .drop(columns=['image_number'])
      .reset_index(drop=True)
    )
    return df
    


def save_shapefile_fom_df(df):
    import geopandas as gpd

    gdf = gpd.GeoDataFrame(
        df.copy(),
        geometry=gpd.points_from_xy(df['longitude'], df['latitude']),
        crs="EPSG:4326"  # WGS84
    )
    rename = {
    'gps_quality': 'gps_qual',
    'number_of_satelites': 'n_satelite',
    'gps_timestamp': 'gps_time',
    'image_datetime': 'img_dt',
    # 'image_path' já tem 10 chars; mantenho
    }
    gdf = gdf.rename(columns=rename)
    
    if 'img_dt' in gdf.columns:
        gdf['img_dt'] = pd.to_datetime(gdf['img_dt'], errors='coerce') \
                      .dt.strftime('%Y-%m-%d %H:%M:%S')
                    
    saida = "teste.shp"  # ajuste o caminho
    gdf.to_file(saida, driver="ESRI Shapefile", encoding="utf-8")
    print(f"Shapefile salvo em: {saida}")



def run_json_folder(trip_id, json_folder, start_image_number= None, final_image_number = None):
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
    
    if start_image_number is not None and final_image_number is not None:
       df = filter_df_by_interval(df, start_image_number, final_image_number)

    # df.head()
    print(df.head())
    
    print(len(df))
    # df.to_excel('trip_teste.xlsx')
    insert_image_data_from_df(trip_id, df)





