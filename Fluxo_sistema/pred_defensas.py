import cv2
import tqdm
import json
import yaml
import os,io
import requests
import pandas as pd
from database_models import ImageData, DefensasDatabase
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger,asc, Table, MetaData, select, join, func
from sqlalchemy.orm import sessionmaker
from multiprocessing import Pool, cpu_count
import re # utilizar em convert_pano_cube
import math
from geopy.distance import great_circle
import numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
from geoalchemy2 import Geometry
from geoalchemy2 import WKTElement
from scipy.ndimage import median_filter
from scipy.ndimage import uniform_filter1d
from collections import Counter
from sqlalchemy.orm import aliased
import uuid

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
    _, buffer = cv2.imencode('.jpg', imagem)
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
                unique_id = 0,
                pred_true = -1,
                image_id=results_dict[convert_cube_to_pano(nome_imagem)].image_id,
                order = results_dict[convert_cube_to_pano(nome_imagem)].order, 
            )
            session.add(defensa) 
    session.commit()
    session.close()

def process_image_data(result):
    file_path = os.path.join(result['path'], result['nome_imagem'])
    if os.path.isfile(file_path):
        data = read_data(file_path)
        prediction = predict(data, list(range(12)))
        return result['nome_imagem'], prediction
    return result['nome_imagem'], None

def run(path,trip_id,trip_direction):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    lados = ['DIREITO','ESQUERDO']
    #tipos_guard = ['%concr%','%met%','%OAE%']

    # Create a metadata instance
    metadata = MetaData()
    # Define the tables
    image_data_with_geom = Table('image_data_with_geom', metadata, autoload_with=engine)

    session = Session() 

    # Create a select query to fetch all rows from the table
    query_images = select(image_data_with_geom)

    #for tipo in tipos_guard:
    for lado in lados:  
        # Execute the query
        results_images = session.execute(query_images).fetchall()

        # Prediction block
        cam = 'cam3'
        if lado == 'DIREITO':
            cam = 'cam1'
        
        result_data = {} 
        tasks = [] 
        for result in results_images: # loop over each guardrail
            tasks.append({'path': path, 
                        'nome_imagem': convert_pano_cube(result.image_name,cam)})
            
        num_cpus = cpu_count()
        with Pool(processes=num_cpus) as pool:
            for nome_imagem, prediction in tqdm.tqdm(pool.imap_unordered(process_image_data, tasks), total=len(tasks)):
                if prediction:
                    # Save results in result_data
                    result_data[nome_imagem] = {
                        'prediction': prediction
                    }

        add_to_db(trip_id, result_data)


################################## compute unique guardrails #######################################
# 1. Clean the noise: Remove isolated 1s or 0s
def clean_noise(vector):
    cleaned_vector = []
    for i in range(len(vector)):
        if i > 0 and i < len(vector) - 1:  # Check for middle elements
            # Keep the element if it's part of a larger group
            if (vector[i] == 1 and (vector[i - 1] == 1 or vector[i + 1] == 1)) or \
               (vector[i] == 0 and (vector[i - 1] == 0 or vector[i + 1] == 0)):
                cleaned_vector.append(vector[i])
        elif i == 0:  # First element
            cleaned_vector.append(vector[i])
        elif i == len(vector) - 1:  # Last element
            cleaned_vector.append(vector[i])
    return cleaned_vector

# 2. Apply smoothing using a simple moving average
def smooth_vector(vector, window_size=3):
    if window_size % 2 == 0:
        window_size += 1  # Ensure window size is odd
    half_window = window_size // 2
    padded_vector = np.pad(vector, (half_window, half_window), mode='edge')  # Pad with edges
    smoothed_vector = []

    for i in range(len(vector)):
        window = padded_vector[i:i + window_size]
        smoothed_value = float(np.mean(window))  # Get the mean and round
        this_val = None
        if vector[i] < 1: # a guardrail should be predicted on this image, but it wasn't
            this_val = smoothed_value
        else:
            this_val = vector[i]
        smoothed_vector.append(this_val)

    return smoothed_vector

def find_detected_elements(smoothed_vector):
    detected_elements = []
    current_element = {}

    idx = 0
    for value in smoothed_vector:
        if value != 0:  # If the value is part of a detection
            current_element[idx] = value
        else:
            if current_element:  # If we have a group of detected elements
                detected_elements.append(current_element)
                current_element = {}  # Reset for the next element
        idx+=1

    if current_element:  # Add the last element if the loop ended with a detected group
        detected_elements.append(current_element)

    return detected_elements

def find_unique_defensas(trip_id,trip_direction):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session() 
    lados = ['DIREITO','ESQUERDO']
    tipos_guard = ['%concr%','%met%']

    # Create a metadata instance
    metadata = MetaData()
    image_data_with_geom = Table('image_data_with_geom', metadata, autoload_with=engine)
    guardrails_details = Table('guardrail_details', metadata, autoload_with=engine)
    guardrail_preds = Table('guardrails_pred', metadata, autoload_with=engine)

    for tipo in tipos_guard:
        for lado in lados:
            cam = 3
            if lado == 'DIREITO':
                cam = 1
            # Define the filtering condition for guardrail_details
            filtered_guardrails = select(
                guardrails_details
            ).where(
                guardrails_details.c.cam == cam,  # Use your specific 'cam' value or variable
                guardrails_details.c.class_name.ilike(tipo)  # Use your specific 'tipo' value or variable
            ).subquery()  # Create a subquery from the filtered guardrail_details

            # Left outer join using outerjoin()
            # You need to specify how the join occurs (e.g., on the image_id field)

            # Select the desired columns from both tables
            query = select(
                filtered_guardrails.c.cam,
                filtered_guardrails.c.class_name,
                filtered_guardrails.c.image_id,
                image_data_with_geom.c.geom
            ).select_from(
                image_data_with_geom.outerjoin(filtered_guardrails, image_data_with_geom.c.image_id == filtered_guardrails.c.image_id)
            )

            # Execute the query and fetch results
            results = session.execute(query).fetchall()

            # aggregate predictions
            prediction_vector = []
            # Iterate through the results and apply the condition
            this_type = None
            for result in results:
                class_name = result[1]  # Assuming class_name is the second column in the result tuple
                if class_name is None:
                    prediction_vector.append(0)
                else:
                    if this_type is None:
                        this_type = class_name
                    prediction_vector.append(1)
            
            clean_prediction_vector = clean_noise(prediction_vector)
            smoothed_vector = smooth_vector(clean_prediction_vector)
            detected_elements = find_detected_elements(smoothed_vector)

            # Iterate through the detected elements (unique guardrails) and prepare insertion into the guardrails_pred table
            for det_el in detected_elements:
                unique_id = str(uuid.uuid4())  # Generate a UUID for the unique guardrail

                # Loop through each image associated with this guardrail (det_el)
                for idx in det_el.keys():
                    # Extract geometry for the current element
                    point = results[idx][3]  # Assuming geom is the 4th column in the result tuple

                    # Prepare the dictionary with the data to insert
                    new_entry = {
                        'km': 0,  # Fill with 0 or null
                        'km_final': 0,  # Fill with 0 or null
                        'sentido': trip_direction,
                        'tipo': this_type,
                        'lado': lado,
                        'geom': point,
                        'pred_true': det_el[idx],
                        'trip_id': trip_id,
                        'unique_id': unique_id  # Same unique_id for all elements of the same detected guardrail
                    }

                    # Insert the row into the database using core insert
                    stmt = guardrail_preds.insert().values(new_entry)
                    session.execute(stmt)

            # Commit the session to save the changes
            session.commit()

                
                    