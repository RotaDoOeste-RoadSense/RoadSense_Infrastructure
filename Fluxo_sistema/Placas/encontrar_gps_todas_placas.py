import yaml
import json
import requests
from geopy.distance import geodesic
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from database_models import ImageData, AllPlatesMatched, PlateDetails, AllGpsCoordinates
from tqdm import tqdm

# Importa função de cache do módulo utilitário
from redis_cache_utils import cache_api_response


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
                    'prev_longitude': prev_image.longitude,
                    'image': current_image.image_name,
                    'prev_image': prev_image.image_name
                }
            )
    return results


def predict_gps(lat, lon, x1, y1, x2, y2, cls):
    """
    Prediz coordenadas GPS com cache Redis.
    Usa cache_api_response para armazenar respostas com TTL 24h.
    """
    # Parâmetros da requisição (serão usados para gerar chave de cache)
    params = {
        'lat': lat,
        'lon': lon,
        'x1': x1,
        'y1': y1,
        'x2': x2,
        'y2': y2,
        'cls': cls
    }

    # Função que executa a requisição (chamada apenas em cache miss)
    def fetch():
        url = cfg['inference_geo_gps']['url']
        error_data = ''
        for i in range(10):  # Tenta 10 vezes antes de levantar um erro
            result = requests.post(url, data=params)
            if result.status_code // 100 == 2:
                try:
                    return result.json()
                except:
                    error_data += f'{result.status_code}: {result.content}\n'
            else:
                error_data += f'{result.status_code}: {result.content}\n'
        print(f'Requisition Error GPS Plate: {error_data}')
        return None

    # Usa cache_api_response do redis_cache_utils
    return cache_api_response('gps_predict', params, fetch)


def run(connection, path, trip_id):
    database_url = cfg['database']['url']
    engine = create_engine(database_url)
    session = sessionmaker(bind=engine)()
    plate_details = get_plate_details_for_trip(session, trip_id)

    for _ in tqdm(plate_details, desc='Placas_GPS'):
        if connection:
            connection.process_data_events()

        result = _['details']
        lat_car, lon_car = float(_['latitude']), float(_['longitude'])
        lat_car_prev, lon_car_prev = float(_['prev_latitude']), float(_['prev_longitude'])
        lat_diff = 1e4 * (lat_car - lat_car_prev)
        lon_diff = 1e4 * (lon_car - lon_car_prev)

        # Usa função com cache em vez de requests.post direto
        response_data = predict_gps(
            lat=lat_diff,
            lon=lon_diff,
            x1=result.x1,
            y1=result.y1,
            x2=result.x2,
            y2=result.y2,
            cls=result.class_value
        )

        # Pula se requisição falhou após retries
        if response_data is None:
            continue

        dlat, dlon = float(response_data['dlat']), float(response_data['dlon'])
        rlat, rlon = lat_car - 1e-4 * dlat, lon_car - 1e-4 * dlon
        distancia = geodesic((lat_car, lon_car), (rlat, rlon)).meters
        geometria = f'SRID=4326;POINT({rlon} {rlat})'

        new_gps = AllGpsCoordinates(
            plate_details_id=result.plate_details_id,
            geom=geometria
        )
        session.add(new_gps)

    session.commit()
    session.close()


if __name__ == '__main__':
    run(None, "/mnt/HD12TB/DATASET_TESTE_RONDONOPOLIS/images", 4)
