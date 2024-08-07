import requests
import folium
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
from pyproj import Transformer
import math
import pandas as pd

def get_road_data(lat, lon):
    '''
    Function to verify if there is a median in the road
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
    return response.json()

def find_ways_in_radius(center_point, radius, df_road):
    """Encontra todas as vias dentro de um determinado raio ao redor de um ponto central."""
    center = Point(center_point)
    ways_in_radius = []

    for index, row in df_road.iterrows():
        way_coords = [(node['lat'], node['lon']) for node in row['geometry']]
        way_line = LineString(way_coords)

        if way_line.distance(center) <= radius:
            ways_in_radius.append(way_line)

    return ways_in_radius

def distance_between_lines(line1, line2):
    """Calcula a distância mínima entre duas linhas, projetando coordenadas para um sistema métrico."""
    # Transformador para projetar coordenadas geográficas para Web Mercator (EPSG:3857)
    transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)

    # Projetar as coordenadas das linhas
    line1_proj = LineString([transformer.transform(*coord) for coord in line1.coords])
    line2_proj = LineString([transformer.transform(*coord) for coord in line2.coords])

    # Encontrar os pontos mais próximos entre as duas linhas
    nearest_points_line1, nearest_points_line2 = nearest_points(line1_proj, line2_proj)

    # Calcular a distância em metros
    distance = nearest_points_line1.distance(nearest_points_line2)

    print(nearest_points_line1.distance(nearest_points_line2))

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

def get_median(lat, lon):
    road_data = get_road_data(lat, lon)
    df_road = pd.DataFrame(road_data['elements'])
    ways_in_radius = find_ways_in_radius((lat, lon), 0.001, df_road)
    # Verifica todas as combinações de vias dentro do raio
    if len(ways_in_radius) < 2:
        return False
    else:
        for i in range(len(ways_in_radius)):
            for j in range(i + 1, len(ways_in_radius)):
                line1 = ways_in_radius[i]
                line2 = ways_in_radius[j]
                if are_lines_parallel(line1, line2):
                    distance = distance_between_lines(line1, line2)
                    return distance