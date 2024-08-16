import tqdm
import json
import yaml
import os,io
import requests
from database_models import ImageData, Estrutura, Trecho, Area
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, asc
from geopy.distance import great_circle
from tqdm import tqdm
from osm import get_highway_number_road_data, get_median
import numpy as np
from multiprocessing import Pool, cpu_count

Base = declarative_base()

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)

def calculate_distance(coord1, coord2):
    return great_circle(coord1, coord2).meters


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

def verify_bridge(coordinates):
    lat, lon = coordinates
    '''
    Function to verify if there is a bridge in the road
    lat: float, latitude
    lon: float, longitude
    '''
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    way(around:40, {lat}, {lon})["highway"];
    out geom;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    road_data = response.json()
    for element in road_data['elements']:
        if 'bridge' in element['tags']:
            return True
    return False

def verify_bridge_osm(coordinates):
    lat, lon = coordinates
    '''
    Function to verify if there is a bridge in the road
    lat: float, latitude
    lon: float, longitude
    '''
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    way(around:40, {lat}, {lon})["highway"];
    out geom;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    road_data = response.json()

    codigo = get_highway_number_road_data(road_data)
    canteiro = get_median(road_data, lat, lon)

    for element in road_data['elements']:
        if 'bridge' in element['tags']:
            return True, codigo, canteiro
    return False, codigo, canteiro

def osm_request(input):

    coordinates = input['coordinates']

    index = input['index']
   
    bridge, cod, canteiro = verify_bridge_osm(coordinates)

    return index, bridge, cod, canteiro 

def is_prf(coordinates):
    lat, lon = coordinates
    # Esta função deve retornar "True" ou "False" como string
    result = {None : None, "False" : False, "True" : True}
    # Esta função deve retornar "True" ou "False" como string
    prf = request_api(lat, lon, 'api_prf_predict')

    return result[prf]

def process_coordinates(coordinates_query, osm):

    codigos = {}

    #sentidos = {}
    canteiros = {}

    #previous_bridge, cod, canteiro = is_bridge(coordinates_query[0])
    previous_bridge, cod, canteiro = osm[0]
    previous_bridge = False
    codigos[0] = cod
    #sentidos[0] = 'N'
    #codigos[0] = 'BR-163'
    canteiros[0] = canteiro

    cumulative_distance = 0

    trechos = {}

    id = 0

    start = None

    if not previous_bridge:
        start = 0

    previous_prf = is_prf(coordinates_query[0])

    structure = None

    if previous_prf:
        structure = 'prf'

    for index in tqdm(range(1, len(coordinates_query))):
        
        current_coordinate = coordinates_query[index]

        if index > 0:
            previous_coordinate = coordinates_query[index - 1]
            distance = calculate_distance(previous_coordinate, current_coordinate)

            actual_bridge, cod, canteiro = osm[index]
            #actual_bridge = False
            codigos[index] = cod
            canteiros[index] = canteiro
            #sentidos[index] = sentido
            #sentidos[index] = 'N'

            actual_prf = is_prf(current_coordinate)
            

            if not (previous_bridge or actual_bridge):
                cumulative_distance += distance

            if previous_bridge and not actual_bridge:
                start = index

            if not previous_bridge and actual_bridge:

                if cumulative_distance > 0:
                    if start != index - 1:
                        trechos[id] = [start, index - 1, cumulative_distance, structure]
                        id += 1
                    structure = None

                # Start a new segment from the current index
                cumulative_distance = distance
                start = index

            if previous_prf and actual_prf and not structure:

                if cumulative_distance > 0:
                    if start != index - 1:
                        trechos[id] = [start, index - 1, cumulative_distance - distance, structure]
                        id += 1
                    structure = None

                structure = 'prf'
                # Start a new segment from the current index
                cumulative_distance = distance
                start = index - 1

            elif not previous_prf and actual_prf and not structure:

                if cumulative_distance > 0:
                    if start != index - 1:
                        trechos[id] = [start, index - 1, cumulative_distance - distance, structure]
                        id += 1
                    structure = None

                structure = 'prf'
                # Start a new segment from the current index
                cumulative_distance = distance
                start = index - 1
        

        if cumulative_distance > 500 and not actual_prf:
                # Close the current segment before exceeding 500 meters
                
                if start != index - 1:
                    trechos[id] = [start, index - 1, cumulative_distance - distance, structure]
                    id += 1
                    structure = None
                # Start a new segment from the current index
                cumulative_distance = distance
                start = index - 1
        
        #print(index, cumulative_distance, previous_bridge, actual_bridge)

        previous_bridge = actual_bridge

        previous_prf = actual_prf


    # Handle the final segment if it does not end in a bridge
    if cumulative_distance > 0:
        if cumulative_distance < 500 or not osm[len(coordinates_query) - 1][0]:
            trechos[id] = [start, len(coordinates_query) - 1, cumulative_distance, structure]

    return trechos, codigos, canteiros


def process_coordinates_central(coordinates_query, canteiros, start_trecho, lastpoint):
    start = None

    trechos_canteiro = {}

    id_canteiro = 0

    cumulative_distance = 0

    prev_canteiro = canteiros[start_trecho]

    if prev_canteiro:
        start = start_trecho
  
    actual_canteiro = None

    for index in range(start_trecho + 1, lastpoint + 1):

        current_coordinate = coordinates_query[index]

        if index > start_trecho:

            previous_coordinate = coordinates_query[index - 1]

            actual_canteiro = canteiros[index]

            distance = calculate_distance(previous_coordinate, current_coordinate)

            if prev_canteiro and actual_canteiro and start is None:

                start = index - 1

            if start is not None:
                cumulative_distance += distance

            if prev_canteiro and not actual_canteiro and start is not None:

                trechos_canteiro[id_canteiro] = [start, index - 1, cumulative_distance - distance]
                id_canteiro += 1
                cumulative_distance = 0
                start = None

        prev_canteiro = actual_canteiro

    if start is not None and canteiros[lastpoint]:
        trechos_canteiro[id_canteiro] = [start, len(range(start_trecho, lastpoint)), cumulative_distance]

    return trechos_canteiro



def determine_direction(coords_inicio, coords_fim):
    lat1, lon1 = coords_inicio
    lat2, lon2 = coords_fim
    """
    Determina a direção do deslocamento entre duas coordenadas geográficas.
    
    Parameters:
    lat1, lon1 -- Latitude e longitude da coordenada inicial
    lat2, lon2 -- Latitude e longitude da coordenada final
    
    Returns:
    'Norte' se o deslocamento foi do sul para o norte,
    'Sul' se o deslocamento foi do norte para o sul
    """
    if lat2 > lat1:
        return 'Norte'
    elif lat2 < lat1:
        return 'Sul'
    else:
        return 'Indefinido'


def run(trip_id):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    coordinates_query = session.query(ImageData.latitude, ImageData.longitude, ImageData.id).filter(ImageData.trip_id == trip_id).order_by(asc(ImageData.order)).all()[:1000]
    coordinates_query = np.array(coordinates_query)



    ids = coordinates_query[:, 2]
    coordinates_query = coordinates_query[:, 0 : 2]

    osm = {}
    indices = [i for i in range(len(coordinates_query))]

    tasks = [{'index' : index, 'coordinates' : coordinates} for index, coordinates in zip(indices, coordinates_query)]

    num_cpus = 6
    with Pool(processes=num_cpus) as pool:
        for index, bridge, cod, canteiro  in tqdm(pool.imap_unordered(osm_request, tasks), total=len(tasks)):
            osm[index] = [bridge, cod, canteiro]

    trechos, codigos, canteiros = process_coordinates(coordinates_query, osm)

    Session = sessionmaker(bind=engine)
    session = Session()


    for j , key in tqdm(enumerate(trechos)):

        start_trecho, lastpoint, distance, structure = trechos[key]

        if not (150 < distance < 800):
            continue

        if j == 0:
            structure = 'teste'

        cod_inicio = codigos[start_trecho]

        cod_fim = codigos[lastpoint]
      
        cod = 'Desconhecido'

        if cod_inicio and cod_fim:
            if cod_inicio != cod_fim:
                cod = cod_inicio + f' {cod_fim}'
            else:
                cod = cod_inicio

        elif cod_inicio or cod_fim:

            if cod_inicio:

                cod = cod_inicio
            else:
                cod = cod_fim

        id_imagem_inicial = ids[start_trecho]

        id_imagem_final = ids[lastpoint]
        
        trecho = Trecho(
            coordenadas_latitude_inicio = coordinates_query[start_trecho][0],
            coordenadas_longitude_inicio = coordinates_query[start_trecho][1],
            coordenadas_latitude_fim = coordinates_query[lastpoint][0],
            coordenadas_longitude_fim = coordinates_query[lastpoint][1],
            codigo_rodovia = cod,
            quilometragem_trecho = distance,
            )
        
        session.add(trecho)
        session.commit()

        if structure:

            estrutura = Estrutura(
                descricao_tipo_estrutura = structure,
                ID_TRECHO = trecho.ID_TRECHO
            )

            session.add(estrutura)
            session.commit()

        sentido = determine_direction(coordinates_query[start_trecho], coordinates_query[lastpoint])

        caracteristicas_area = 'lateral_' +  sentido

        area = Area(
            caracteristicas_area = caracteristicas_area,
            id_imagem_inicio = id_imagem_inicial,
            id_imagem_fim = id_imagem_final,
            ID_TRECHO = trecho.ID_TRECHO,
        )

        session.add(area)
        
        tem_true_no_intervalo = any(canteiros[chave] for chave in range(start_trecho, lastpoint + 1))

        if tem_true_no_intervalo:
            print(f'tem canteiro central')
            
            trechos_canteiro = process_coordinates_central(coordinates_query, canteiros, start_trecho, lastpoint)

            for j , key in tqdm(enumerate(trechos_canteiro)):

                start, lastpoint, distance = trechos_canteiro[key]

                if not (20 < distance < 800):
                    continue

                caracteristicas_area = 'canteiro_' +  sentido

                id_imagem_inicial = ids[start]

                id_imagem_final = ids[lastpoint]

                area = Area(
                    caracteristicas_area = caracteristicas_area,
                    id_imagem_inicio = id_imagem_inicial,
                    id_imagem_fim = id_imagem_final,
                    ID_TRECHO = trecho.ID_TRECHO,
                )

                session.add(area)

        
        session.commit()

    session.close()
    
    