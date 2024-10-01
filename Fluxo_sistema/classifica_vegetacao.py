from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, asc
import yaml
import requests
import json
import re
import numpy as np
import os, io, cv2
from database_models import Trip, ImageData, Area, Vegetacao, Manutencao
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

Base = declarative_base()

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)

def request_api(lat, lon, api_name):
    
    url = cfg[api_name]['url']
    output_name = cfg[api_name]['output']
    data = {'lat' :lat , 'lon' : lon}
    error_data = ''
    for i in range(10):  # Tenta 10 vezes antes de levantar um erro
            result = None
            try:
                result = requests.post(url, data=data)
            except Exception as e:
                error_data += f'erro: {e}'
                continue

            if result.status_code // 100 == 2:
                try:
                    return json.loads(result.text)[output_name]
                except:
                    error_data += f'{result.status_code}: {result.content}\n'
            else:
                error_data += f'{result.status_code}: {result.content}\n'

def modify_filename(image_name, new_type, insertion_string):
    # Divide o nome do arquivo em partes
    base_name, extension = image_name.rsplit('.', 1)
    
    # Localiza o termo 'Panoramic' e a sequência de 6 dígitos subsequente
    match = re.search(r'(Panoramic_\d{6})_', base_name)
    
    if match:
        # Obtém o prefixo que inclui 'Panoramic' e os 6 dígitos
        prefix = match.group(1)
        
        # Divide a base_name em partes ao redor do prefixo
        before_prefix = base_name.split(prefix)[0]
        after_prefix = base_name.split(prefix)[1]
        
        # Monta o novo nome base
        new_base_name = f"{before_prefix}{prefix}_{insertion_string}{after_prefix}"
        
        # Monta o novo nome de arquivo
        new_image_name = f"{new_base_name}.{extension}"
        return new_image_name.replace('Panoramic', 'Cube')
    else:
        # Retorna o nome original se 'Panoramic' não for encontrado
        return None

def get_image_Cube_path(folder, image_name, lateral='direita'):

    if 'lateral' in lateral:
        cam_id = 1
    elif 'canteiro' in lateral:
        cam_id = 3
    else:
        return None

    prefix = os.path.join(folder, 'Cube') 
    image_name = modify_filename(image_name, 'Cube', f'Cam{cam_id}')
    if image_name:
        image_name = os.path.join(prefix, image_name)
    else:
        return None
    
    return image_name



def get_image_Cube_path2(folder, image_name, lateral='direita'):

    if 'lateral' in lateral:
        cam_id = 1
    elif 'canteiro' in lateral:
        cam_id = 3
    else:
        return None

    prefix = os.path.join(folder, 'Cube') 
    image_name = image_name.split('.')[0] + f'_cam{cam_id}.jpg'
    image_name = image_name.replace('Panoramic', 'Cube')
    if image_name:
        image_name = os.path.join(prefix, image_name)
    else:
        return None
    
    return image_name

def read_data(file_name, area):
    imagem = cv2.imread(file_name)
    height, width = imagem.shape[:2]
    if 'esquerda' in area:
        imagem = imagem[:, 1*width//16:7*width//16]
    else:
        imagem = imagem[:, 9*width//16:15*width//16]

    if imagem is None:
        raise ValueError(f"Não foi possível ler a imagem {file_name}")
    _, buffer = cv2.imencode('.jpg', imagem)
    imagem_bytes = io.BytesIO(buffer).getvalue()
    return imagem_bytes



def predict(file_data):
    url = cfg['inference_vegetacao']['url']
    files = {"file": ("image.jpg", file_data, "image/jpeg")}
    error_data = ''
    for i in range(10):  # Tenta 10 vezes antes de levantar um erro
        result = requests.post(url, files=files)
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

class_to_peso = {
        0: 5,
        1: 0,
        2: 3,
    }
def get_peso(class_id):
    return class_to_peso.get(class_id, 0)

def calcular_manutencao (classifications):
    cls_image = [ 0 , 0 , 0, 0 ]

    for classification in classifications:
        scr, cls, lbl = classification

        if (scr < 0.5):
            continue
        
        cls_image[lbl] += 1

    soma = 0
    for i in range(0, len(cls_image)):
            soma += cls_image[i]*get_peso(i)

    divisor = (sum(cls_image)*get_peso(0))

    if divisor > 0:
        score_trecho = soma/divisor
    else:
        score_trecho = -1

    return score_trecho

def process_image_data(input):
    file_path = input['image_path']
    id = input['image_id']
    area = input['area']
    data = read_data(file_path, area)

    prediction = predict(data)
    return file_path, prediction, id

def run(trip_id):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    areas_query = session.query(Area.area_id, Area.start_image_id, Area.end_image_id, Area.area_characteristics, Area.section_id).all()

    areas_query = np.array(areas_query)
    #ids_list = areas_query[:, 0]

    folder = session.query(Trip.root_folder).filter(Trip.trip_id == trip_id).all()[0][0]
    
    for element in areas_query:
        id_area, id_ini, id_fim, area, id_trecho = element
        
        classifications = []

        #MOCANDO A AREA POR ENQUANTO PRA SER IGUAL A NORTE
        #area = 'direita'
        ids_area = [id for id in range(int(id_ini), int(id_fim) + 1)]
        images_query = session.query(ImageData.image_id, ImageData.image_name).filter(ImageData.trip_id == trip_id, ImageData.image_id.in_(ids_area)).order_by(asc(ImageData.order)).all()
        images_list = []

        c = 0
        
        for image in images_query:
            id_image, image_name = image
          
            image_path = folder + '/Panoramic/' + image_name+'.jpg'
            #print(image_path_Cube)
            if os.path.exists(image_path):
                c += 1
                images_list.append([id_image, image_path])
            else:
                print(f'nao existe a imagem {image_path}')
       
        if c != len(images_query): # Garante o número correto de classificações
            continue

        result_data = {}

        tasks = [{'image_id' : path[0], 'image_path': path[1], 'area' : area} for path in images_list]
        num_cpus = cpu_count()
        with Pool(processes=num_cpus) as pool:
            for image_path, prediction, image_id in tqdm(pool.imap_unordered(process_image_data, tasks), total=len(tasks)):
                result_data[image_path] = [prediction, image_id]
        
        for key in result_data:

            classification = result_data[key][0]
            image_id = result_data[key][1]
            scr = classification['Score']
            cls = classification['Classificação']
            lbl = classification['Label']

            filename = os.path.basename(key)


            vegetacao = Vegetacao (
                image_file_name= filename,
                prediction = cls,
                score = scr,
                area_id = int(id_area),
                image_id = image_id
            )

            session.add(vegetacao)

            classifications.append((scr, cls, lbl))

        session.commit()

        score_trecho = calcular_manutencao(classifications)

        data = session.query(Trip.timestamp).filter(Trip.trip_id == trip_id).all()[0][0]

        
        manutencao = Manutencao (
            date = data,
            state = score_trecho,
            area_id = id_area
        )

        session.add(manutencao)
        session.commit()

        
    session.close()


#run(2)