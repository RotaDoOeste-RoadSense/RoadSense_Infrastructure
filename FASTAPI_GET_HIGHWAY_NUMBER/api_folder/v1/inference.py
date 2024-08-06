import requests

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

def get_highway_number(lat, lon):
    """
    Get highway number from road data
    lat: float - latitude
    lon: float - longitude
    """
    road_data = get_road_data(lat, lon)
    for element in road_data['elements']:
        if 'ref' in element['tags']:
            if 'BR-364' in element['tags']['ref']:
                return 'BR-364'
            elif 'BR-163' in element['tags']['ref']:
                return 'BR-163'
            return element['tags']['ref'] 
    return None
