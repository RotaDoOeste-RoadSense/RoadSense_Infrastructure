import requests

def get_median(lat, lon):
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

    # median?
    cantr = False
    if len(road_data['elements']) > 1:
        cantr = True
    return cantr
