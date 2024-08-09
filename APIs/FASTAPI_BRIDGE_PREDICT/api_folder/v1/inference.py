import requests

def verify_bridge(lat, lon):
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

