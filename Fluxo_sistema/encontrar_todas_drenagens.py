import cv2
import tqdm
import json
import yaml
import os,io
import requests
import pandas as pd
from database_models import ImageData, DrenagensDatabase
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger,asc, Table, MetaData, select, func
from sqlalchemy.orm import sessionmaker
from multiprocessing import Pool, cpu_count
import re # utilizar em convert_pano_cube
import math
from geopy.distance import great_circle
import numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
from geoalchemy2 import Geometry
from scipy.ndimage import median_filter
from scipy.ndimage import uniform_filter1d
from collections import Counter
from sqlalchemy.orm import aliased

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

def find_unique(data):
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
    url = cfg['inference_drenagem']['url']
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
    result_data = {convert_cube_to_pano(nome_imagem):drenagens_data for nome_imagem, drenagens_data in result_data.items() if drenagens_data}
    Session = sessionmaker(bind=engine)
    session = Session()
    results = session.query(ImageData).filter(ImageData.trip_id == trip_id,ImageData.image_name.in_(tuple(result_data.keys()))).order_by(asc(ImageData.order)).all()
    results_dict = {result.image_name:result for result in results}
    table_relation_drenagem_img_id = {}

    for nome_imagem, drenagens_data in result_data_orig.items():
        for drenagem_data in drenagens_data['prediction']:
            if 'prob' in drenagem_data.keys(): # if a prediction was made
                drenagem = DrenagensDatabase(
                    class_value=drenagem_data['class'],
                    class_name=drenagem_data['class_name'], 
                    prob=drenagem_data['prob'], 
                    cam=int(extract_camera_number(nome_imagem)),
                    x1=drenagem_data['xyxyn'][0], 
                    y1=drenagem_data['xyxyn'][1], 
                    x2=drenagem_data['xyxyn'][2], 
                    y2=drenagem_data['xyxyn'][3], 
                    image_id=results_dict[convert_cube_to_pano(nome_imagem)].image_id,
                    unique_id = int(drenagens_data['drainage_id']),  
                    order = results_dict[convert_cube_to_pano(nome_imagem)].order, 
                    pred_true = drenagens_data['pred_true'] 
                )
            else:
                drenagem = DrenagensDatabase(
                    class_value=None,
                    class_name=drenagem_data['class_name'], 
                    prob=0, 
                    cam=int(extract_camera_number(nome_imagem)),
                    x1=0, 
                    y1=0, 
                    x2=0, 
                    y2=0, 
                    image_id=results_dict[convert_cube_to_pano(nome_imagem)].image_id,
                    unique_id = int(drenagens_data['drainage_id']),  
                    order = results_dict[convert_cube_to_pano(nome_imagem)].order, 
                    pred_true = drenagens_data['pred_true'] 
                )
            session.add(drenagem) 
    session.commit()
    session.close()

def process_image_data(result):
    file_path = os.path.join(result['path'], result['nome_imagem'])
    if os.path.isfile(file_path):
        data = read_data(file_path)
        prediction = predict(data, list(range(12)))
        return result['nome_imagem'], prediction, result['drainage_id']
    return result['nome_imagem'], None, result['drainage_id']

def apply_smoothing(result_data):
    drainage_groups = {}
    # Organize predictions by drainage_id
    prediction_class_name = ""
    for nome_imagem, data in result_data.items():
        drainage_id = data['drainage_id']
        # store detected classes
        pred_true = 0 # assume that a prediction of a drainage from type tipo was not made...
        for this_data in data['prediction']:
            if this_data['class_name']: # a prediction of a drainage from type tipo was made...
                pred_true = 1
                prediction_class_name = this_data['class_name']

        # initialize drainage group
        if drainage_id not in drainage_groups: 
            drainage_groups[drainage_id] = []

        # append data to a drainage group
        drainage_groups[drainage_id].append((nome_imagem, pred_true))

    # Apply median smoothing for each drainage_id
    for drainage_id, drainage_predictions in drainage_groups.items():
        # Sort the entries by nome_imagem (assuming it's ordered lexicographically)
        drainage_predictions.sort(key=lambda x: x[0])

        # Extract the 'pred_true' values for filtering
        pred_true_values = [pred for _, pred in drainage_predictions]

        # Apply a filter for a given 1D window size
        #smoothed_preds = uniform_filter1d(pred_true_values, size=3)
        wnd_size = max(int(len(pred_true_values)/2),1) # wind size is always > 1
        smoothed_preds = np.convolve(pred_true_values,(np.ones(wnd_size)/wnd_size),mode='same')
        
        # Update the result_data with the smoothed predictions
        for (nome_imagem, pred_true), smoothed_pred in zip(drainage_predictions, smoothed_preds):
            if not pred_true: # if this image is nearby a drainage and is not associated with a prediction, then...
                result_data[nome_imagem]['prediction'] = [{"class_name": prediction_class_name}]
                result_data[nome_imagem]['pred_true'] = float(smoothed_pred)

    return result_data

def run(path,trip_id,trip_direction):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    #lados = ['DIREITO','ESQUERDO']
    #tipos_guard = ['%concr%','%met%','%OAE%']

    # Create a metadata instance
    metadata = MetaData()
    # Define the tables
    drainage_cro_evelop = Table('drainages_cro_evelop', metadata, autoload_with=engine)
    image_data_with_geom = Table('image_data_with_geom', metadata, autoload_with=engine)

    session = Session() 

    # Construct the query to select drainages, considering lado and tipo
    drainage_eval = (
        select(
            drainage_cro_evelop.c.rnum,
            drainage_cro_evelop.c.id,
            drainage_cro_evelop.c.geom,
            drainage_cro_evelop.c.sentido
        )
        .where(
            drainage_cro_evelop.c.sentido.ilike(trip_direction)
        )
    )

    # Convert the  drainage_eval into a subquery
    drainage_eval_subquery = drainage_eval.subquery()

    # get images associated with a trip_id....
    # Assuming you have your table classes defined appropriately
    filtered_images = (
        select(
            image_data_with_geom.c.image_name,
            image_data_with_geom.c.geom,
            image_data_with_geom.c.trip_id,  # Include any other necessary columns
            # Add more columns as needed
        )
        .select_from(image_data_with_geom)  # Assuming image_data_with_geom is a mapped class
        .where(image_data_with_geom.c.trip_id == trip_id)  # Replace with your input trip_id
    ).cte('filtered_images')  # Create the CTE


    # Alias for the drainage_eval_subquery for clarity
    drainage_eval = aliased(drainage_eval_subquery)

    # Main query using the CTE
    query_grouped = (
        select(
            drainage_eval.c.id.label("drainage_id"),  # Group by drainage ID
            func.array_agg(filtered_images.c.image_name).label("image_names"),  # Aggregate image names
            func.array_agg(func.ST_AsText(filtered_images.c.geom)).label("geoms"),  # Aggregate geometries as WKT
            func.count().label("num_images")  # Count the number of images per drainage
        )
        .select_from(filtered_images)
        .join(
            drainage_eval,
            func.ST_Intersects(drainage_eval.c.geom, filtered_images.c.geom)  # Spatial join based on geometry intersection
        )
        .group_by(drainage_eval.c.id)  # Group by the drainage ID
    )


    # Execute the query
    results_grouped_images = session.execute(query_grouped).fetchall()

    # Prediction block
    cam = 'cam0'
    
    result_data = {} 
    tasks = [] 
    for result in results_grouped_images: # loop over each drainage
        for image_name in result.image_names: # loop over each image associated with this drainage
            tasks.append({'path': path, 
                        'nome_imagem': convert_pano_cube(image_name,cam), 
                        'drainage_id': result.drainage_id})
    num_cpus = cpu_count()
    with Pool(processes=num_cpus) as pool:
        for nome_imagem, prediction, drainage_id in tqdm.tqdm(pool.imap_unordered(process_image_data, tasks), total=len(tasks)):
            pred_true = 0 # assume no prediction was made...
            if prediction:
                pred_true = 1 # something was predicted...
                
            # Save results in result_data
            result_data[nome_imagem] = {
                'prediction': prediction,
                'pred_true': pred_true,
                'drainage_id': drainage_id
            }
    # Example: Apply smoothing 
    result_data_final = apply_smoothing(result_data.copy())
    add_to_db(trip_id, result_data_final)


if __name__=='__main__':
    run("/mnt/HD12TB/DATASET_TESTE_RONDONOPOLIS/images",4)  