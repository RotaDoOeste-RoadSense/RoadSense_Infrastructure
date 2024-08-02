import requests

def get_median(lat, lon):
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
    road_data = response.json()
    num_ways = len(road_data['elements'])
    if num_ways < 2:
        # not central median
        return False
    return True
    