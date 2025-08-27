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

database_url = cfg["database"]["url"]
engine = create_engine(database_url)


def request_api(lat, lon, api_name):

    url = cfg[api_name]["url"]
    output_name = cfg[api_name]["output"]
    data = {"lat": lat, "lon": lon}
    error_data = ""
    for i in range(10):  # Tenta 10 vezes antes de levantar um erro
        result = None
        try:
            result = requests.post(url, data=data)
        except Exception as e:
            error_data += f"erro: {e}"
            continue

        if result.status_code // 100 == 2:
            try:
                return json.loads(result.text)[output_name]
            except:
                error_data += f"{result.status_code}: {result.content}\n"
        else:
            error_data += f"{result.status_code}: {result.content}\n"


def modify_filename(image_name, new_type, insertion_string):
    # Divide o nome do arquivo em partes
    base_name, extension = image_name.rsplit(".", 1)

    # Localiza o termo 'Panoramic' e a sequência de 6 dígitos subsequente
    match = re.search(r"(Panoramic_\d{6})_", base_name)

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
        return new_image_name.replace("Panoramic", "Cube")
    else:
        # Retorna o nome original se 'Panoramic' não for encontrado
        return None


def get_image_Cube_path(folder, image_name, lateral="direita"):

    if "lateral" in lateral:
        cam_id = 1
    elif "canteiro" in lateral:
        cam_id = 3
    else:
        return None

    prefix = os.path.join(folder, "Cube")
    image_name = modify_filename(image_name, "Cube", f"Cam{cam_id}")
    if image_name:
        image_name = os.path.join(prefix, image_name)
    else:
        return None

    return image_name


def get_image_Cube_path2(folder, image_name, lateral="direita"):

    if lateral == 'direita':
        cam_id = 1
    elif lateral == 'esquerda':
        cam_id = 3
    else:
        return None

    prefix = os.path.join(folder, "Cube")
    image_name = image_name.split(".")[0] + f"_cam{cam_id}.jpg"
    image_name = image_name.replace("Panoramic", "Cube")
    if image_name:
        image_name = os.path.join(prefix, image_name)
    else:
        return None

    return image_name


def get_image_binary(image):
    _, buffer = cv2.imencode(".jpg", image)
    image_bytes = io.BytesIO(buffer).getvalue()

    return image_bytes


# def read_data(file_name):
#     imagem = cv2.imread(file_name)
#     height, width = imagem.shape[:2]

#     imagem_esquerda = imagem[:, 1 * width // 16 : 7 * width // 16]
#     imagem_direita = imagem[:, 9 * width // 16 : 15 * width // 16]

#     if imagem_esquerda is None or imagem_direita is None:
#         raise ValueError(f"Não foi possível ler a imagem {file_name}")

#     return get_image_binary(imagem_esquerda), get_image_binary(imagem_direita)



def read_data(file_name, folder):
    filename_panoramic = file_name.split('/')[-1]

    path_direita = get_image_Cube_path2(folder, filename_panoramic, 'direita')
    path_esquerda = get_image_Cube_path2(folder, filename_panoramic, 'esquerda')

    #imagem = cv2.imread(file_name)
    #height, width = imagem.shape[:2]
    # imagem_esquerda = imagem[:, 1 * width // 16 : 7 * width // 16]
    # imagem_direita = imagem[:, 9 * width // 16 : 15 * width // 16]
    imagem_esquerda = cv2.imread(path_esquerda)
    imagem_direita = cv2.imread(path_direita)

    if imagem_esquerda is None or imagem_direita is None:
        raise ValueError(f"Não foi possível ler a imagem {path_direita},{path_esquerda}")

    return get_image_binary(imagem_esquerda), get_image_binary(imagem_direita)


def predict(file_data):
    url = cfg["inference_vegetacao_cube"]["url"]
    files = {"file": ("image.jpg", file_data, "image/jpeg")}
    error_data = ""
    for i in range(10):  # Tenta 10 vezes antes de levantar um erro
        result = requests.post(url, files=files)
        if result.status_code // 100 == 2:
            try:
                # print(result.text,json.loads(result.text))
                return json.loads(result.text)
            except:
                #print('ERRO na api')
                error_data += f"{result.status_code}: {result.content}\n"
        else:
            error_data += f"{result.status_code}: {result.content}\n"
    # Substitua este erro por um logger adequado
    #print("Deu erro na requisição: " + error_data)
    
    

class_to_peso = {
    0: 5,
    1: 0,
    2: 3,
}

def get_peso(class_id):
    return class_to_peso.get(class_id, 0)

def calcular_score(classifications):
    cls_image = [0, 0, 0]
    for classification in classifications:
        scr, cls, lbl = classification
        if scr < 0.5:
            continue
        cls_image[lbl] += 1

    soma = 0
    for i in range(len(cls_image)):
        soma += cls_image[i] * get_peso(i)

    divisor = sum(cls_image) * get_peso(0)
    if divisor > 0:
        return soma / divisor
    else:
        return -1


def calcular_manutencao_lados(classifications_esquerda, classifications_direita):

    # Calcula o score para cada lado
    score_esquerda = calcular_score(classifications_esquerda)
    score_direita = calcular_score(classifications_direita)

    return score_esquerda, score_direita


def process_image_data(input):
    file_path = input["image_path"]
    id = input["image_id"]
    folder = input["folder"]
    data_esquerda, data_direita = read_data(file_path, folder)

    prediction_esquerda = predict(data_esquerda)
    prediction_direita = predict(data_direita)
    return file_path, prediction_esquerda, prediction_direita, id


def run(connection, trip_id):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    areas_query = session.query(
        Area.area_id, Area.start_image_id, Area.end_image_id, Area.section_id
    ).filter(ImageData.image_id == Area.start_image_id, ImageData.trip_id == trip_id).all()

    areas_query = np.array(areas_query)
    # ids_list = areas_query[:, 0]
  
    folder = session.query(Trip.root_folder).filter(Trip.trip_id == trip_id).all()[0][0]

    #folder = '/mnt/windows_share/GPS_sul'
    #folder_split = folder.split('/mnt/windows_share/')[-1]
    #folder_split2 = folder_split.split('/')[0]
    #folder = os.path.join('/mnt/windows_share/',folder_split2)
    
    for element in tqdm(areas_query, desc='Vegetacao_predict'):
        id_area, id_ini, id_fim, id_trecho = element

        cam_left = 3
        cam_right = 1

        classifications = []
        classifications_left = []
        classifications_right = []

        ids_area = [id for id in range(int(id_ini), int(id_fim) + 1)]
        images_query = (
            session.query(ImageData.image_id, ImageData.image_name)
            .filter(ImageData.trip_id == trip_id, ImageData.image_id.in_(ids_area))
            .order_by(asc(ImageData.order))
            .all()
        )
        images_list = []

        c = 0

        for image in images_query:
            id_image, image_name = image

            image_path = folder + "/Cube/" + image_name
            
            images_list.append([id_image, image_path])
            # print(image_path_Cube)
            # if os.path.exists(image_path):
            #     c += 1
            #     
            # else:
            #     print(f"nao existe a imagem {image_path}")

        # if c != len(images_query):  # Garante o número correto de classificações
        #     continue

        result_data = {}

        # tasks = [{'image_id' : path[0], 'image_path': path[1], 'area' : area} for path in images_list]
        tasks = [{"image_id": img[0], "image_path": img[1], "folder" : folder} for img in images_list]
        

        num_cpus = cpu_count()
        group_size = 20
        grouped = [tasks[i:i + group_size] for i in range(0, len(tasks), group_size)]
    
        for group in grouped:

            with Pool(processes=num_cpus) as pool:
                for image_path, prediction_left, prediction_right, image_id in pool.map(process_image_data, group):
                    classifications.append(
                            (
                                image_path,
                                image_id,
                                prediction_left["Score"],
                                prediction_right["Score"],
                                prediction_left["Classificação"],
                                prediction_right["Classificação"],
                                prediction_left["Label"],
                                prediction_right["Label"],
                            )
                        )
                    connection.process_data_events()

        assert len(tasks) == len(classifications)
        for key in classifications:
            if len(key) != 8:
                print(key)
    
        for key in classifications:
            image_path = key[0]
            image_id = key[1]
            scr_lft = key[2]
            scr_rgt = key[3]
            cls_lft = key[4]
            cls_rgt = key[5]
            lbl_lft = key[6]
            lbl_rgt = key[7]

            filename = os.path.basename(image_path)

            vegetacao = Vegetacao(
                image_file_name_left=filename.replace("Panoramic", "Cube")[:-4]
                + f"_cam{cam_left}.jpg",
                image_file_name_right=filename.replace("Panoramic", "Cube")[:-4]
                + f"_cam{cam_right}.jpg",
                prediction_left=cls_lft,
                prediction_right=cls_rgt,
                score_left=scr_lft,
                score_right=scr_rgt,
                area_id=int(id_area),
                image_id=image_id,
            )

            session.add(vegetacao)

            classifications_left.append((scr_lft, cls_lft, lbl_lft))
            classifications_right.append((scr_rgt, cls_rgt, lbl_rgt))
            connection.process_data_events()
        session.commit()

        score_trecho_esquerdo, score_trecho_direito = calcular_manutencao_lados(
            classifications_left, classifications_right
        )

        data = session.query(Trip.timestamp).filter(Trip.trip_id == trip_id).all()[0][0]

        #print(data, score_trecho_esquerdo, score_trecho_direito, id_area)

        manutencao = Manutencao(
            date=data,
            state_left=score_trecho_esquerdo,
            state_right=score_trecho_direito,
            area_id=int(id_area),
        )
        session.add(manutencao)
        session.commit()
        connection.process_data_events()

    session.close()


# run(2)
