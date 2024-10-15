import tqdm
import json
import math
import yaml
import os,io
import requests
import pandas as pd
from database_models import ImageData, Estrutura, Trecho, Area, KM_CRO
from database_models import Trip
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, asc, func
from geopy.distance import great_circle
from tqdm import tqdm
import numpy as np
from multiprocessing import Pool, cpu_count

Base = declarative_base()

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)

csv_estruturas = 'pontos_estruturas.csv'


def calculate_distance(coord1, coord2):
    distance = great_circle(coord1, coord2).meters
    #if distance < 1000:
    #    print(distance)
    return distance


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


# Função que faz o resquest de qual os kms 
def request_api_km(trip_id, lat, lon):
    url = cfg['api_km_nearest']['url']
    params = {'trip_id' : trip_id, 'lat' : lat, 'lon' : lon}
    error_data = ''
    for i in range(10):  # Tenta 10 vezes antes de levantar um erro
        result = requests.get(url, params=params)
        if result.status_code // 100 == 2:
            try:
                return json.loads(result.text)
            except:
                error_data += f'{result.status_code}: {result.content}\n'
        else:
            error_data += f'{result.status_code}: {result.content}\n'
    print('Deu erro na requisição (KM): ' + error_data)

# Função que retorna o km, seguindo a lógica 
def get_km (lat1, lon1, lat2, lon2, trip_id):
    saida1 = request_api_km(trip_id, lat1, lon1)
    saida2 = request_api_km(trip_id, lat2, lon2)

    if  not ('closest' in saida1) or not ('closest' in saida2):
        return 'Erro'

    if saida1 is None and saida2 is None:
        return 'None'
    elif saida1 is None:
        return saida2['closest'][0]  
    elif saida2 is None:
        return saida1['closest'][0] 
    elif saida1['closest'][0]  == saida2['closest'][0]:
        return saida1['closest'][0]; 
    else:
        return f"{saida1['closest'][0]}-{saida2['closest'][0]}"

# Verifica se dois pontos estão próximos dados uma distância mínima
def esta_proximo (coords1, coords2, minDist):
    distance2 = calculate_distance(coords1, coords2)

    return True if distance2 <= minDist else False

# Verifica quais estruturas estão próximas dado um .csv com as coordenadas delas.
df = pd.read_csv(csv_estruturas)
def verificar_proximidade(coords_orig, min_dist):
    
    for coluna in df.columns:
        for _, linha in df.iterrows():
            coords = linha[coluna]
         
            if pd.notna(coords):
                try:
                    lon, lat = map(float, coords.split())
                    coords2 = (lat, lon)
                    
                    proximidade = esta_proximo(coords_orig, coords2, min_dist)
                    if proximidade:
                        return (True, coluna) if coluna != 'pontes' else (False, None) 
                except ValueError:
                    continue

    return False, None


def process_coordinates(coordinates_query):


    #sentidos = {}
    

    #previous_bridge, cod, canteiro = is_bridge(coordinates_query[0])
    #previous_bridge, cod, canteiro = osm[0]
    #previous_bridge = False

    #sentidos[0] = 'N'
    #codigos[0] = 'BR-163'
  

    cumulative_distance = 0

    trechos = {}

    id = 0

    start = None
   
    start = 0

    #lat, lon = coordinates_query[0]

    # Distância mínima para ser considerado próximo
    minDist = 100
    
    previous_prf = verificar_proximidade(coordinates_query[0], minDist)

    structure = None

    if previous_prf[0]:
        structure = previous_prf[1]

    for index in tqdm(range(1, len(coordinates_query))):
        
        current_coordinate = coordinates_query[index]

        if index > 0:
            

            previous_coordinate = coordinates_query[index - 1]
            distance = calculate_distance(previous_coordinate, current_coordinate)

            actual_prf = verificar_proximidade(current_coordinate, minDist)
     
            cumulative_distance += distance

            if previous_prf[0] and actual_prf[0] and not structure:

                if cumulative_distance > 0:
                    if start != index - 1:
                        trechos[id] = [start, index - 1, cumulative_distance - distance, structure]
                        id += 1
                    structure = None

                structure = previous_prf[1]
                # Start a new segment from the current index
                cumulative_distance = distance
                start = index - 1

            elif not previous_prf[0] and actual_prf[0] and not structure:

                if cumulative_distance > 0:
                    if start != index - 1:
                        trechos[id] = [start, index - 1, cumulative_distance - distance, structure]
                        id += 1
                    structure = None

                structure = actual_prf[1]
                # Start a new segment from the current index
                cumulative_distance = distance
                start = index - 1

            elif previous_prf[0] and not actual_prf[0] and structure:

                if cumulative_distance > 0:
                    if start != index - 1:
                        trechos[id] = [start, index - 1, cumulative_distance - distance, structure]
                        id += 1
                    structure = None

                structure = None
                # Start a new segment from the current index
                cumulative_distance = distance
                start = index - 1
        
        if cumulative_distance > 500 and not actual_prf[0]:
            # Close the current segment before exceeding 500 meters
            
            if start != index - 1:
                trechos[id] = [start, index - 1, cumulative_distance - distance, structure]
                id += 1
                structure = None
            # Start a new segment from the current index
            cumulative_distance = distance
            start = index - 1
        
        previous_prf = actual_prf


    # Handle the final segment if it does not end in a bridge
    if cumulative_distance > 0:
        if cumulative_distance < 500:
            trechos[id] = [start, len(coordinates_query) - 1, cumulative_distance, structure]

    return trechos

'''
def calcular_distancia(session, latitude, longitude, distancia_maxima, limite=1):
    ponto = f'SRID=4326;POINT({longitude} {latitude})'
    
    # Transformando o ponto para uma projeção métrica
    ponto_metrico = func.ST_Transform(func.ST_GeomFromText(ponto), 3857)
    
    resultados = session.query(KM_CRO,  func.ST_Distance(func.ST_Transform(KM_CRO.geom, 3857), ponto_metrico) \
                               .label('distancia')).order_by('distancia').limit(10).all()

    
    return resultados
'''
'''
def calcular_distancia(session, latitude, longitude, distancia_maxima, limite=1):
    ponto = f'SRID=4326;POINT({longitude} {latitude})'
    
    # Transformando o ponto para uma projeção métrica
    ponto_metrico = func.ST_Transform(func.ST_GeomFromText(ponto), 3857)
    
    resultados = session.query(KM_CRO).filter(
        func.ST_Distance(
            func.ST_Transform(KM_CRO.geom, 3857), 
            ponto_metrico
        ) <= distancia_maxima).limit(10).all()

    print(resultados)
    exit()
    
    return resultados
'''

def calcular_distancia(session, latitude, longitude, distancia_maxima):
    ponto = f'SRID=4326;POINT({longitude} {latitude})'
    
    # Transformando o ponto para uma projeção métrica
    ponto_metrico = func.ST_Transform(func.ST_GeomFromText(ponto), 3857)
    
    # Consulta para calcular a distância e filtrar dentro do limite
    resultado = session.query(
        KM_CRO,
        func.ST_Distance(func.ST_Transform(KM_CRO.geom, 3857), ponto_metrico).label('distancia')
    ).order_by('distancia').first()  # Retorna apenas o primeiro resultado (menor distância)

    if resultado is None:
        print("Nenhum resultado encontrado dentro do limite especificado.")
    else:
        km_cro, distancia = resultado

        if distancia > 100:
            resultado = None
        print(f"Resultado encontrado: Rodovia: {km_cro.rodovia}, Distância: {distancia} metros")

    return resultado

def run(trip_id):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    coordinates_query = session.query(ImageData.latitude, ImageData.longitude, ImageData.image_id).filter(ImageData.trip_id == trip_id).order_by(asc(ImageData.order)).all()
   
    coordinates_query = np.array(coordinates_query)



    ids = coordinates_query[:, 2]
    coordinates_query = coordinates_query[:, 0 : 2]

    osm = {}
    indices = [i for i in range(len(coordinates_query))]

    tasks = [{'index' : index, 'coordinates' : coordinates} for index, coordinates in zip(indices, coordinates_query)]

    latitudes = coordinates_query[:, 0]

    longitudes = coordinates_query[:, 1]

    geometries = session.query(KM_CRO.km, KM_CRO.rodovia, KM_CRO.latitude, KM_CRO.longitude).all()

    #result = calcular_distancia(session, lat, lon, 100)
    trechos = process_coordinates(coordinates_query)

    Session = sessionmaker(bind=engine)
    session = Session()

    way = session.query(Trip.way).filter(Trip.trip_id == trip_id).all()[0][0]

    
    if way == 'N':
        sentido = 'Norte'
         
    elif way == 'S':
        sentido = 'Sul'
    
    else:
        sentido = 'Indefinido'
    
    caracteristicas_area_direita = 'Lateral_Direita_' + sentido

    caracteristicas_area_esquerda = 'Lateral_Esquerda_' + sentido

  

    for j , key in tqdm(enumerate(trechos)):

        start_trecho, lastpoint, distance, structure = trechos[key]

        if not (150 < distance < 800):
            continue

        #if j == 0:
        #    structure = 'teste'
        cod = 'Desconhecido'

        # Faz a requisão para a api sobre qual km se localiza o trecho.
        lat_start, lon_start = coordinates_query[start_trecho]
        km_start = calcular_distancia(session, lat_start, lon_start, 100)

        lat_end, lon_end = coordinates_query[lastpoint]
        km_end = calcular_distancia(session, lat_end, lon_end, 100)

        print(km_start, km_end)

        #if len(km_start) > 0 and len(km_end) > 0:
        if km_start is not None and km_end is not None:
            
            cod = km_start[0].rodovia + '_' + km_end[0].rodovia

            km = str(km_start[0].km) + '_' + str(km_end[0].km)
        else:
            km = get_km(coordinates_query[start_trecho][0], coordinates_query[start_trecho][1],
                        coordinates_query[lastpoint][0], coordinates_query[lastpoint][1], trip_id)

        #elif len(km_start) > 0:

        '''
        elif km_start is not None:
            cod = km_start[0].rodovia 

            km = str(km_start[0].km)
        # elif len(km_end) > 0:
        elif km_end is not None:
            cod = km_end[0].rodovia 

            km = str(km_end[0].km)
        '''
      
        id_imagem_inicial = ids[start_trecho]

        id_imagem_final = ids[lastpoint]
        
        trecho = Trecho(
            start_latitude_coordinates = float(coordinates_query[start_trecho][0]),
            start_longitude_coordinates = float(coordinates_query[start_trecho][1]),
            end_latitude_coordinates = float(coordinates_query[lastpoint][0]),
            end_longitude_coordinates = float(coordinates_query[lastpoint][1]),
            highway_code = cod,
            section_mileage = km,
            )
        
        session.add(trecho)
        session.commit()

        if structure:

            estrutura = Estrutura(
                structure_type_description = structure,
                section_id = trecho.section_id
            )

            session.add(estrutura)
            session.commit()

        #caracteristicas_area = 'lateral_direita' 

        area = Area(
            start_image_id = int(id_imagem_inicial),
            end_image_id = int(id_imagem_final),
            section_id = trecho.section_id,
        )

        session.add(area)
        
        #caracteristicas_area = 'lateral_esquerda'
        
        session.commit()

    session.close()
    
    