import cv2
import tqdm
import json
import yaml
import os,io
import requests
import pandas as pd
from database_models import ImageData, DefensasDatabase
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger,asc
from sqlalchemy.orm import sessionmaker
from multiprocessing import Pool, cpu_count
import re # utilizar em convert_pano_cube
import math
from geopy.distance import great_circle
import numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle

Base = declarative_base()

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)

# Function to calculate distance matrix using Haversine formula
def haversine_distance_matrix(coords):
    num_coords = len(coords)
    distance_matrix = np.zeros((num_coords, num_coords))
    for i in range(num_coords):
        for j in range(num_coords):
            if i != j:
                distance_matrix[i, j] = great_circle(coords[i], coords[j]).meters
    return distance_matrix

def find_unique_guardrails(data):
    result_data = data.copy()
    # Convert data to a list of coordinates
    coords = [(value['lat'], value['lon']) for value in result_data.values()]

    # Compute distance matrix
    distance_matrix = haversine_distance_matrix(coords)

    dbscan = DBSCAN(eps=8, min_samples=1, metric='precomputed')
    dbscan_clusters = dbscan.fit_predict(distance_matrix)

    # Output clusters for DBSCAN
    dbscan_clustered_points = {}
    for idx, label in enumerate(dbscan_clusters):
        image_name = list(result_data.keys())[idx]
        if label not in dbscan_clustered_points:
            dbscan_clustered_points[label] = []
        dbscan_clustered_points[label].append(image_name)
    
    # Sort image names lexicographically and assign unique_id and order
    for cluster_id, image_names in dbscan_clustered_points.items():
        # Sort image names lexicographically
        image_names_sorted = sorted(image_names)
        
        # Update result_data with the lexicographical order and unique_id (cluster_id)
        for order, image_name in enumerate(image_names_sorted, start=1):
            result_data[image_name]['order'] = order
            result_data[image_name]['unique_id'] = cluster_id
    
    return result_data

def extract_camera_number(image_name):
    # Regular expression to match 'Cam' or 'cam' followed by digits
    match = re.search(r'_[cC]am(\d)', image_name)
    if match:
        return match.group(1)  # Return the matched digits
    return None  # Return None if no match is found

def convert_pano_cube(pano_img_name,cam):
    return re.sub(r'Panoramic_(\d{6})',f'Cube_\\1_'+cam,pano_img_name)

def convert_cube_to_pano(cube_img_name):
    return re.sub(r'Cube_(\d{6})_[cC]am[0-6]', r'Panoramic_\1', cube_img_name)

def read_data(file_name):
    imagem = cv2.imread(file_name)
    if imagem is None:
        raise ValueError(f"Não foi possível ler a imagem {file_name}")
    altura, largura, _ = imagem.shape
    imagem_crop = imagem[:, 5*largura//16:11*largura//16]
        # import matplotlib.pyplot as plt
        # plt.imshow(imagem_crop)
        # plt.show()
    _, buffer = cv2.imencode('.jpg', imagem_crop)
    imagem_bytes = io.BytesIO(buffer).getvalue()
    return imagem_bytes

def predict(file_data, classes=None):
    url = cfg['inference_defensa']['url']
    files = {"file": ("image.jpg", file_data, "image/jpeg")}
    data = {"classes": ','.join(map(str, classes))} if classes else {}
    error_data = ''
    for i in range(10):  # Tenta 10 vezes antes de levantar um erro
        result = requests.post(url, files=files, data=data)
        if result.status_code // 100 == 2:
            try:
                return json.loads(result.text)
            except:
                error_data += f'{result.status_code}: {result.content}\n'
        else:
            error_data += f'{result.status_code}: {result.content}\n'
    # Substitua este erro por um logger adequado
    print('Deu erro na requisição: ' + error_data)

def add_to_db(trip_id, result_data):
    result_data_orig = result_data.copy()
    result_data = {convert_cube_to_pano(nome_imagem):defensas_data for nome_imagem, defensas_data in result_data.items() if defensas_data}
    #result_data = {nome_imagem:defensas_data for nome_imagem, defensas_data in result_data.items() if defensas_data}
    Session = sessionmaker(bind=engine)
    session = Session()
    results = session.query(ImageData).filter(ImageData.trip_id == trip_id,ImageData.image_name.in_(tuple(result_data.keys()))).order_by(asc(ImageData.order)).all()
    results_dict = {result.image_name:result for result in results}
    table_relation_guardrail_img_id = {}
    '''
    for result in results:
        _ = AllDefensasMatched(image_id=result.image_id)
        session.add(_)
        session.flush()
        table_relation_guardrail_img_id[result.image_id] = _.all_guardrail_matched_id
    '''

    for nome_imagem, defensas_data in result_data_orig.items():
        # tem que converter xyxy aqui...
        #print(int(extract_camera_number(nome_imagem)))
        for defensa_data in defensas_data['prediction']:
            defensa = DefensasDatabase(
                class_value=defensa_data['class'],
                class_name=defensa_data['class_name'], 
                prob=defensa_data['prob'], 
                cam=int(extract_camera_number(nome_imagem)),
                x1=defensa_data['xyxyn'][0], 
                y1=defensa_data['xyxyn'][1], 
                x2=defensa_data['xyxyn'][2], 
                y2=defensa_data['xyxyn'][3], 
                image_id=results_dict[convert_cube_to_pano(nome_imagem)].image_id,
                unique_id = int(defensas_data['unique_id']),  
                order = defensas_data['order']  
            )
            session.add(defensa) 
    session.commit()
    session.close()

def process_image_data(result):
    file_path = os.path.join(result['path'], result['nome_imagem'])
    if os.path.isfile(file_path):
        data = read_data(file_path)
        prediction = predict(data, list(range(12)))
        return result['nome_imagem'], prediction, result['lon'], result['lat']
    return result['nome_imagem'], None, result['lon'], result['lat']

def run(path,trip_id):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session() 
    results = session.query(ImageData).filter(ImageData.trip_id == trip_id).order_by(asc(ImageData.order)).all()
    #cam1
    
    result_data = {} 
    tasks = [] 
    for results in results:
        tasks.append({'path': path, 'nome_imagem': convert_pano_cube(results.image_name,'cam1'), 'lat': results.latitude, 'lon': results.longitude})
    num_cpus = cpu_count()
    with Pool(processes=num_cpus) as pool:
        for nome_imagem, prediction, lon, lat in tqdm.tqdm(pool.imap_unordered(process_image_data, tasks), total=len(tasks)):
            if prediction:
                # Save results in result_data
                result_data[nome_imagem] = {
                    'prediction': prediction,
                    'lon': lon,
                    'lat': lat
                }
    result_data_final = find_unique_guardrails(result_data)
    add_to_db(trip_id, result_data_final)
    '''
    #cam3
    result_data = {} 
    tasks = [] 
    for results in results:
        print(convert_pano_cube(results.image_name,'cam3'))
        tasks.append({'path': path, 'nome_imagem': convert_pano_cube(results.image_name,'cam3'), 'lat': results.latitude, 'lon': results.longitude})
    num_cpus = cpu_count()
    with Pool(processes=num_cpus) as pool:
        for nome_imagem, prediction, lon, lat in tqdm.tqdm(pool.imap_unordered(process_image_data, tasks), total=len(tasks)):
            if prediction:
                # Save results in result_data
                result_data[nome_imagem] = {
                    'prediction': prediction,
                    'lon': lon,
                    'lat': lat
                }
    result_data_final = find_unique_guardrails(result_data)
    add_to_db(trip_id, result_data_final)
    '''
if __name__=='__main__':
    run("/mnt/HD12TB/DATASET_TESTE_RONDONOPOLIS/images",4)  