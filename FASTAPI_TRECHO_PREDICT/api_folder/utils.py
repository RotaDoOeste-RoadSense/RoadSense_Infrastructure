from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
import requests
from rapidfuzz import fuzz

def nearest_polyline(lat, lng, polylines):
    point = Point(lat, lng)
    point_min_distance = None
    nearest_id = None
    min_distance = float('inf')
    for id, line in polylines.items():
        # Find the nearest point on the line
        nearest_point = nearest_points(point, line)
        nearest_point = nearest_point[1]

        distance = point.distance(nearest_point)
        if distance < min_distance:
            min_distance = distance
            nearest_id = id
            point_min_distance = nearest_point
    
    return min_distance, point_min_distance, nearest_id


def find_most_similar_ref(uncertain_id, lat, lon):
    # Query for Overpass API to fetch road data
    test_point = [lat, lon]
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    way(around:10, {test_point[0]}, {test_point[1]})["highway"];
    out geom;
    """

    # Make request to Overpass API
    response = requests.get(overpass_url, params={'data': overpass_query})
    road_data = response.json()

    # get similar refs
    refs_list = []
    for element in road_data['elements']:
        elements_raw = element['tags']['ref'].split(';') # lista de BRs associadas
        refs_list.extend([ref_br for ref_br in elements_raw]) 
    similarities = [fuzz.ratio(uncertain_id, id) for id in refs_list]
    most_similar_index = similarities.index(max(similarities))
    return refs_list[most_similar_index]
