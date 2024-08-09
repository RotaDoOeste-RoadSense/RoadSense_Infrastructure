import requests
from shapely.geometry import Point, LineString

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
        print(road_data['elements'][0]['tags'])
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