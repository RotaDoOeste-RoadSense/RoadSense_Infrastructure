import requests
from shapely.geometry import Point, LineString
from pyproj import Transformer
import math
import pandas as pd
from shapely.ops import nearest_points

def get_road_data(lat, lon):
    """
    Get road data from Overpass API
    lat: float - latitude
    lon: float - longitude
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    way['highway'](around:40, {lat},{lon});
    out geom;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    return response.json()

def is_north_or_south_duplicated_highways(lat, lon, element):
    """
    to check if a point is on the left side of a line
    lat: float - latitude
    lon: float - longitude
    element: dict - road data element
    """
    points = [(node['lat'], node['lon']) for node in element['geometry']]
    if points:
        # Determine the direction of the line
        start_lat, end_lat = points[0][0], points[-1][0]
        if end_lat < start_lat:
            return "S"  # South
        else:
            return "N"  # North

def is_point_on_left(line, point):
    """
    to check if a point is on the left side of a line
    line: LineString - road line
    point: Point - input point
    """
    # extract start and end coordinates
    start = line.coords[0]
    end = line.coords[-1]

    # calculate vectors
    vector_line = (end[0] - start[0], end[1] - start[1])  # line vector
    vector_point = (point.x - start[0], point.y - start[1])  # point vector

    # calculate cross product
    cross_product = vector_line[0] * vector_point[1] - vector_line[1] * vector_point[0]

    return cross_product > 0  # if positive, point is on the left

def is_north_or_south_simple_highways(lat, lon, road_data):
    """
    to check if a point is on the left side of a line
    lat: float - latitude
    lon: float - longitude
    road_data: dict - road data
    """
    # list to store LineStrings
    linestrings = []
    # iteration over elements of road data
    for element in road_data['elements']:
        #print(road_data['elements'][0]['tags'])
        if element['tags'].get('oneway') == 'no':
            points = [(node['lat'], node['lon']) for node in element['geometry']]
            if points:
                # LineString creation
                line = LineString([(lon, lat) for lat, lon in points])
                linestrings.append(line)
                
                # to verify if the point is on the left side of the line
                input_point = Point(lon, lat)
                if is_point_on_left(line, input_point):
                    return "N"
                else:
                    return "S"

def is_north_or_south(lat, lon):
    """
    to check if a point of the road is going to the north or south
    lat: float - latitude
    lon: float - longitude
    """
    road_data = get_road_data(lat, lon)
    exclusions = ['service']
    for element in road_data['elements']:
        if element['tags']['highway'] not in exclusions and 'oneway' in element['tags']:
            if element['tags']['oneway'] == 'yes':
                return is_north_or_south_duplicated_highways(lat, lon, element)
            else:
                return is_north_or_south_simple_highways(lat, lon, road_data)
            
def is_north_or_south_road_data(road_data, lat, lon):
    
    exclusions = ['service']
    for element in road_data['elements']:
        if element['tags']['highway'] not in exclusions and 'oneway' in element['tags']:
            if element['tags']['oneway'] == 'yes':
                return is_north_or_south_duplicated_highways(lat, lon, element)
            else:
                return is_north_or_south_simple_highways(lat, lon, road_data)

def get_highway_number_road_data(road_data):
    """
    Get highway number from road data
    lat: float - latitude
    lon: float - longitude
    """
    for element in road_data['elements']:
        if 'ref' in element['tags']:
            if 'BR-364' in element['tags']['ref']:
                return 'BR-364'
            elif 'BR-163' in element['tags']['ref']:
                return 'BR-163'
            return element['tags']['ref'] 
    return None

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

def get_median(road_data, lat, lon):
    #road_data = get_road_data(lat, lon)
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