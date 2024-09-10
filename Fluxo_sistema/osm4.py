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


def distance_between_lines(line1_proj, line2_proj):
 
    # Encontrar os pontos mais próximos entre as duas linhas
    nearest_points_line1, nearest_points_line2 = nearest_points(line1_proj, line2_proj)

    # Calcular a distância em metros
    distance = nearest_points_line1.distance(nearest_points_line2)

    if distance > 0 and distance < 7:
        return False

    elif distance > 7 and distance < 30:
        return True

    elif distance > 30:
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

def are_lines_parallel(line1, line2, tolerance=1.0):
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

    for index, (way_line, road_name) in enumerate(ways_proj):
        
        # Calcular a distância do centro da via ao ponto de referência
        way_center = way_line.centroid
        distance = way_center.distance(ref_proj_point)
        if distance < radius_meters:
            ways_with_distance.append((index, way_line, distance, road_name))

    ways_with_distance.sort(key=lambda x: x[2])

    sorted_ways_proj = [y[1] for y in ways_with_distance]

    return sorted_ways_proj, ways_with_distance[0][3]

transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)

def get_median(road_data_proj, lat, lon):

    # Transformar o ponto de referência para coordenadas projetadas
    ref_x, ref_y = transformer.transform(lon, lat)
    ref_proj_point = Point(ref_x, ref_y)

    ways_in_radius, road_name = order_and_filter_ways(road_data_proj, ref_proj_point, 100)

    # Verifica todas as combinações de vias dentro do raio
    if len(ways_in_radius) < 2:
        return False, road_name
    else:
        distances = []
        aux = False
        for i in range(len(ways_in_radius)):
            for j in range(i + 1, len(ways_in_radius)):
                line1 = ways_in_radius[i]
                line2 = ways_in_radius[j]
                if are_lines_parallel(line1, line2):
                    distance = distance_between_lines(line1, line2)
                    if distance:
                        aux = True             
        return aux, road_name
                    