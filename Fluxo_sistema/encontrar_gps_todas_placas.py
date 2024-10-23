import yaml
import json
import requests
from geopy.distance import geodesic
#from database_models import create_tables
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, BigInteger, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, joinedload
from sqlalchemy.orm import aliased
from database_models import ImageData, Trip, AllPlatesMatched, PlateDetails, AllGpsCoordinates

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
Base = declarative_base()


def get_plate_details_for_trip(session, trip_id):
    images = session.query(
        ImageData
    ).filter(
        ImageData.trip_id == trip_id
    ).order_by(
        ImageData.order
    ).all()
    results = []
    for idx in range(1, len(images)):
        current_image = images[idx]
        prev_image = images[idx - 1]
        plate_details = session.query(
            PlateDetails
        ).join(
            AllPlatesMatched, AllPlatesMatched.all_plates_matched_id == PlateDetails.all_plates_matched_id
        ).filter(
            AllPlatesMatched.image_id == current_image.image_id
        ).all()
        for details in plate_details:
            results.append(
                {
                    'details': details,
                    'latitude': current_image.latitude,
                    'longitude': current_image.longitude,
                    'prev_latitude': prev_image.latitude,
                    'prev_longitude': prev_image.longitude
                }
            )
    return results

def predict(_input):
    url = cfg['inference_gps']['url']
    error_data = ''
    for i in range(10):  # Tenta 10 vezes antes de levantar um erro
        data={'lat':_input[0],
        'lon':_input[1],
        'x1':_input[2],
        'y1':_input[3],
        'x2':_input[4],
        'y2':_input[5],
        'cls':_input[6]}
        result = requests.post(url, data=data)
        if result.status_code // 100 == 2:
            try:
                return json.loads(result.text)
            except:
                error_data += f'{result.status_code}: {result.content}\n'
        else:
            error_data += f'{result.status_code}: {result.content}\n'
    print('Deu erro na requisição: ' + error_data)

def run(path,trip_id):
    new_gps_relations = {}
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    database_url = cfg['database']['url']
    engine = create_engine(database_url)
    #create_tables(engine)
    session = sessionmaker(bind=engine)()
    plate_details = get_plate_details_for_trip(session, trip_id)
    for _ in plate_details:
        result,lat_car,lon_car,lat_car_prev,lon_car_prev = _['details'],float(_['latitude']),float(_['longitude']),float(_['prev_latitude']),float(_['prev_longitude'])
        lat_diff = 1e4*(lat_car-lat_car_prev)
        lon_diff = 1e4*(lon_car-lon_car_prev)
        response = requests.post(cfg['inference_gps']['url'],data={
            'lat': lat_diff,
            'lon': lon_diff,
            'x1': result.x1,
            'y1': result.y1,
            'x2': result.x2,
            'y2': result.y2,
            'cls': result.class_value
        })
        dlat,dlon = float(response.json()['dlat']),float(response.json()['dlon'])
        rlat,rlon = lat_car-1e-4*dlat,lon_car-1e-4*dlon
        # print(geodesic((lat_car,lon_car),(rlat,rlon)).meters)
        new_gps = AllGpsCoordinates(
            plate_details_id=result.all_plates_matched_id,
            lat=rlat,
            lon=rlon
        )
        session.add(new_gps)
    session.commit()
    
if __name__=='__main__':
    run("/mnt/HD12TB/DATASET_TESTE_RONDONOPOLIS/images",4)