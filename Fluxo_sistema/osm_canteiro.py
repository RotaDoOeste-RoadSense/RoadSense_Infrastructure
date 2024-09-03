import requests
import folium
import json
from osm4 import get_median
from tqdm import tqdm
from time import time
import pandas as pd
from multiprocessing import Pool, cpu_count
from pyproj import Transformer
from shapely.geometry import Point, LineString

def fetch_road_data(bbox):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      way
      ["highway"]({bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]});
    );
    out geom;
    """
    
    response = requests.get(overpass_url, params={'data': overpass_query})
    if response.status_code == 200:
        data = response.json()
         # Filtrar elementos que têm geometria
        #elements_with_geometry = [element for element in data['elements'] if 'geometry' in element]
        #data['elements'] = elements_with_geometry
        return data
    else:
        raise Exception(f"Error fetching data: {response.status_code}")
    

def process_canteiro(input):

    ways_proj = input['road_data_proj']
    lat, lon = input['coordinates']
  
    index = input['index']

    return index, get_median(ways_proj, lat, lon)


def sort_key(line):
    line = line[0]
    if line.is_empty:
        return (float('inf'), float('inf'))  # Coloca linhas vazias no final
    start_point = line.coords[0]
    return start_point  # Ordena por coordenada inicial
    

bbox = [-17.5199188, -56.5249848, -11.6928061, -54.6431911]

road_data = fetch_road_data(bbox)


delete = []

ways = road_data['elements']

transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)

processed_ways_proj = []

for way in ways:
    if 'ref' in way['tags']:
        road_name = way['tags']['ref']
        if 'BR' in road_name:
            way_coords_proj = [transformer.transform(node['lon'], node['lat']) for node in way['geometry']]
            processed_ways_proj.append([LineString(way_coords_proj), road_name]) 

processed_ways_proj = sorted(processed_ways_proj, key=sort_key)

lat, lon = -17.5199188, -56.5249848

lat, lon = -15.619725876913622, -56.06673502490779


start = time()
for j in tqdm(range(100)):
    canteiro, road_name = get_median(processed_ways_proj,  lat, lon)
#canteiro = get_median(road_data,  lat, lon)


tempo = time() - start
print(canteiro)
print(f'processing_time is {tempo} s')



from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, asc
from database_models import ImageData
import yaml
import numpy as np

Base = declarative_base()

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)

trip_id = 3

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
coordinates_query = session.query(ImageData.latitude, ImageData.longitude, ImageData.image_id).filter(ImageData.trip_id == trip_id).order_by(asc(ImageData.order)).all()
coordinates_query = np.array(coordinates_query) [ :1000]

ids = coordinates_query[:, 2]
coordinates_query = coordinates_query[:, 0 : 2]

canteiros = {}

osm = {}


num_cpus = 4
indices = [i for i in range(len(coordinates_query))]

tasks = [{'index' : index, 'coordinates' : coordinates,'road_data_proj' : processed_ways_proj} for index, coordinates in zip(indices, coordinates_query)]

with Pool(processes=num_cpus) as pool:
    for index, result  in tqdm(pool.imap_unordered(process_canteiro, tasks), total=len(tasks)):
        osm[index] = result

print(osm)
