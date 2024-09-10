import requests
from shapely.geometry import Point, LineString
from pyproj import Transformer
import math
import pandas as pd
from shapely.ops import nearest_points
import bisect
import numpy as np
import random
import folium
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from geopy.distance import geodesic

transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)

#bbox - lat, lon,(inicio) lat, lon(fim)
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
        return data
    else:
        raise Exception(f"Error fetching data: {response.status_code}")
    

def sort_key(line):
    line = line[0]
    if line.is_empty:
        return (float('inf'), float('inf'))  # Coloca linhas vazias no final
    start_point = line.coords[0]
    return start_point  # Ordena por coordenada inicial


def get_ways(road_data):

    processed_ways_proj = []

    ways = road_data['elements']

    for way in ways:
        if 'ref' in way['tags']:
            road_name = way['tags']['ref']
            oneway = True
            if 'oneway' in way['tags']:
                oneway = way['tags']['oneway']
                #print(oneway)
                if oneway == 'no':
                    oneway = False
            if 'BR' in road_name:
                way_coords_proj = [transformer.transform(node['lon'], node['lat']) for node in way['geometry']]
                way_coords = [(node['lon'], node['lat']) for node in way['geometry']]
                processed_ways_proj.append([LineString(way_coords_proj), road_name, oneway]) 

    processed_ways_proj = sorted(processed_ways_proj, key=sort_key)

    return processed_ways_proj


def distance_between_points(point1, point2):
    # Calcular a distância em metros
    distance = point1.distance(point2)

    #print(f'distance = {distance}')

    if distance > 0 and distance < 7:
        return False

    elif distance > 7  and distance < 60:
        return True

    elif distance > 60:
        return False

    return None


def calculate_angle(line):
    """Calcula o ângulo de uma linha em relação ao eixo horizontal."""
    x1, y1 = line.coords[0]
    x2, y2 = line.coords[-1]
    delta_x = x2 - x1
    delta_y = y2 - y1
    angle = math.degrees(math.atan2(delta_y, delta_x))
    return angle

def are_lines_parallel(line1, line2, tolerance=10.0):
    """Verifica se duas linhas são paralelas dentro de uma certa tolerância."""
    angle1 = calculate_angle(line1)
    angle2 = calculate_angle(line2)
    difference = abs(angle1 - angle2)
    return difference < tolerance or difference > (180 - tolerance)

def order_and_filter_ways(ways_proj, ref_proj_point, radius_meters):
    """Ordena as vias pela distância ao ponto de referência e filtra aquelas que estão fora do raio especificado."""
    # Criar um transformador para converter de coordenadas geográficas (WGS84) para coordenadas projetadas (UTM por exemplo)
    ways_with_distance = []

    distance_result = {}

    distances = []

    road_names = []

    for index, (way_line, road_name, oneway) in enumerate(ways_proj):

        distance = ref_proj_point.distance(way_line)
        distances.append(distance)
        road_names.append((distance, road_name))
        if distance < radius_meters and oneway:
            ways_with_distance.append((index, way_line, distance, road_name))
            

    ways_with_distance.sort(key=lambda x: x[2])

    road_names.sort(key=lambda x: x[0])

    sorted_ways_proj = [y[1] for y in ways_with_distance]
    
    if len(road_names) > 0:

        return sorted_ways_proj, road_names[0][1]
    else: 
        return sorted_ways_proj, 'indefinido'


def vector_from_line(line):
    """Retorna o vetor diretor da linha."""
    if not isinstance(line, LineString):
        print(line)
        raise TypeError("A entrada deve ser uma instância de LineString do shapely.")
    x1, y1 = line.coords[0]
    x2, y2 = line.coords[-1]
    return np.array([x2 - x1, y2 - y1])


def extract_segments_near_point(line, point, buffer_radius):
    """Extrai segmentos da linha que estão dentro de um buffer ao redor do ponto."""
    segments = []
    coords = list(line.coords)
    for i in range(len(coords) - 1):
        segment = LineString([coords[i], coords[i + 1]])
        if segment.distance(point) < buffer_radius:
            segments.append(segment)
    return segments


def check_parallelism_at_point(line1a, line2a, point, buffer_radius=100, tolerance=1):
    """Verifica se duas linhas são paralelas em torno de um ponto dentro de um buffer."""
    buffer_point = point.buffer(buffer_radius)

    if not isinstance(line1a, LineString) or not isinstance(line2a, LineString):
        raise TypeError("As entradas devem ser instâncias de LineString do shapely.")
    
    
    # Extrair segmentos próximos ao ponto
    segments1 = extract_segments_near_point(line1a, point, buffer_radius)
    segments2 = extract_segments_near_point(line2a, point, buffer_radius)

    distance_point_line1 = line1a.project(point)
    projected_point_line1 = line1a.interpolate(distance_point_line1)

    distance_point_line2 = line2a.project(point)
    projected_point_line2 = line2a.interpolate(distance_point_line2)

    valid_distance = distance_between_points(projected_point_line1, projected_point_line2)

    if not segments1 or not segments2 or not valid_distance:
        return False  # Nenhum segmento encontrado na área de interesse
    
    # Calcular vetores e verificar paralelismo
    for seg1 in segments1:
        vec1 = vector_from_line(seg1)
        for seg2 in segments2:
            vec2 = vector_from_line(seg2)
            if are_lines_parallel(seg1, seg2):
                return True
    return False


def get_median(road_data_proj, lat, lon):

    # Transformar o ponto de referência para coordenadas projetadas
    ref_x, ref_y = transformer.transform(lon, lat)
    ref_proj_point = Point(ref_x, ref_y)

    ways_in_radius, road_name = order_and_filter_ways(road_data_proj, ref_proj_point, 100)

    if len(ways_in_radius) < 2:
        return road_name, False
    else:
        distances = []
        aux = False
        for i in range(len(ways_in_radius)):
            for j in range(i + 1, len(ways_in_radius)):
                line1 = ways_in_radius[i]
                line2 = ways_in_radius[j]
                if check_parallelism_at_point(line1, line2, ref_proj_point):
                    aux = True             
        return road_name, aux
                    