import cv2
import tqdm
import json
import yaml
import os,io
import requests
import pandas as pd
from database_models import ImageData, AllDefensasMatched, DefensasDatabase,create_tables
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger,asc
from sqlalchemy.orm import sessionmaker
from multiprocessing import Pool, cpu_count
import re # utilizar em convert_pano_cube

Base = declarative_base()

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)

def extract_camera_number(image_name):
    # Regular expression to match 'Cam' followed by digits
    match = re.search(r'_Cam(\d)_', image_name)
    if match:
        return match.group(1)  # Return the matched digits
    return None  # Return None if no match is found

def convert_pano_cube(pano_img_name,cam):
    return re.sub(r'Panoramic_(\d{6})',f'Cube_\\1_'+cam,pano_img_name)

def convert_cube_to_pano(cube_img_name):
    return re.sub(r'Cube_(\d{6})_Cam[0-6]', r'Panoramic_\1', cube_img_name)

def inverse_projection_bbox(bbox, face, face_width, face_height, pano_width, pano_height):
    """
    Convert a bounding box from a side view (left or right) cube face back to an equirectangular (panoramic) image.
    
    Args:
    - bbox: (x1, y1, x2, y2) bounding box in the cube face image.
    - face: The face ID ('cam1' for left, 'cam3' for right).
    - face_width: Width of the cube face image.
    - face_height: Height of the cube face image.
    - pano_width: Width of the panoramic image.
    - pano_height: Height of the panoramic image.
    
    Returns:
    - panoramic_bbox: (pano_x1, pano_y1, pano_x2, pano_y2) bounding box in the equirectangular (panoramic) image.
    """

    x1, y1, x2, y2 = bbox
    
    # Inverse project the top-left corner
    pano_x1, pano_y1 = inverse_projection_side_view(x1, y1, face, face_width, face_height, pano_width, pano_height)
    
    # Inverse project the bottom-right corner
    pano_x2, pano_y2 = inverse_projection_side_view(x2, y2, face, face_width, face_height, pano_width, pano_height)
    
    return (pano_x1, pano_y1, pano_x2, pano_y2)

def inverse_projection_side_view(x, y, face, face_width, face_height, pano_width, pano_height):
    """
    Convert coordinates from a side view (left or right) cube face back to an equirectangular (panoramic) image.
    
    Args:
    - x, y: Coordinates in the cube face image.
    - face: The face ID ('cam1' for left, 'cam3' for right).
    - face_width: Width of the cube face image.
    - face_height: Height of the cube face image.
    - pano_width: Width of the panoramic image.
    - pano_height: Height of the panoramic image.
    
    Returns:
    - pano_x, pano_y: Coordinates in the equirectangular (panoramic) image.
    """
    # Convert x, y to normalized coordinates in the cube face
    u = (x / face_width) * 2 - 1  # Range: [-1, 1]
    v = (y / face_height) * 2 - 1 # Range: [-1, 1]

    if face == 'Cam1':  # Left-side view (-90 degrees)
        theta = -math.pi / 2  # -90 degrees in radians
    elif face == 'Cam3':  # Right-side view (+90 degrees)
        theta = math.pi / 2  # +90 degrees in radians

    # Compute the corresponding direction vector on the unit sphere
    X = math.cos(theta)
    Y = v
    Z = -u * X  # Adjust based on horizontal orientation

    # Normalize the direction vector
    magnitude = math.sqrt(X * X + Y * Y + Z * Z)
    X /= magnitude
    Y /= magnitude
    Z /= magnitude

    # Convert the direction vector to spherical coordinates
    phi = math.atan2(Y, math.sqrt(X * X + Z * Z))  # Latitude (phi)
    lambda_ = math.atan2(Z, X) + theta  # Longitude (lambda) adjusted for side view

    # Normalize spherical coordinates to equirectangular coordinates
    pano_x = (lambda_ / math.pi + 1) * pano_width / 2  # Scale to [0, pano_width]
    pano_y = (phi / (math.pi / 2)) * pano_height / 2 + pano_height / 2  # Scale to [0, pano_height]

    return pano_x, pano_y

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
                # print(result.text,json.loads(result.text))
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
    results_dict = {result.nome_imagem:result for result in results}
    table_relation_guardrail_img_id = {}
    
    for result in results:
        
        _ = AllDefensasMatched(image_id=result.image_id)
        session.add(_)
        session.flush()
        table_relation_guardrail_img_id[result.id] = _.id

    for nome_imagem, defensas_data in result_data_orig.items():
        # tem que converter xyxy aqui...
        for defensa_data in defensas_data:
            #print(table_relation_guardrail_img_id[results_dict[nome_imagem].id])
            print(nome_imagem)
            print(extract_camera_number(nome_imagem))
            print(results_dict[convert_cube_to_pano(nome_imagem)].id)
            defensa = DefensasDatabase(
                    class_value=defensa_data['class'],
                    class_name=defensa_data['class_name'], 
                    prob=defensa_data['prob'], 
                    cam = extract_camera_number(nome_imagem),
                    x1=defensa_data['xyxyn'][0], 
                    y1=defensa_data['xyxyn'][1], 
                    x2=defensa_data['xyxyn'][2], 
                    y2=defensa_data['xyxyn'][3], 
                    image_id = table_relation_guardrail_img_id[results_dict[convert_cube_to_pano(nome_imagem)].id]
                )
            session.add(defensa) 
    session.commit()
    session.close()

def process_image_data(result):
    file_path = os.path.join(result['path'], result['nome_imagem'])
    data = read_data(file_path)
    prediction = predict(data, list(range(12)))
    return result['nome_imagem'], prediction 

def run(path,trip_id):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session() 
    results = session.query(ImageData).filter(ImageData.trip_id == trip_id).order_by(asc(ImageData.order)).all()
    result_data = {} 
    tasks = [] 
    for results in results[:50]:
        tasks.append({'path': path, 'nome_imagem': convert_pano_cube(results.nome_imagem,'Cam1')})
        tasks.append({'path': path, 'nome_imagem': convert_pano_cube(results.nome_imagem,'Cam3')})
    num_cpus = cpu_count()
    with Pool(processes=num_cpus) as pool:
        for nome_imagem, prediction in tqdm.tqdm(pool.imap_unordered(process_image_data, tasks), total=len(tasks)):
            result_data[nome_imagem] = prediction
    add_to_db(trip_id, result_data)

if __name__=='__main__':
    run("/mnt/HD12TB/DATASET_TESTE_RONDONOPOLIS/images",4)