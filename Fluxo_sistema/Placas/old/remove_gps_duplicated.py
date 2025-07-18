import os
import yaml
import pandas as pd
from collections import defaultdict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_models import PlateDetails,AllGpsCoordinates

def agrupar_sublistas_por_id(lista):
    grupos = defaultdict(list)
    for sublista in lista:
        id = sublista[0]
        grupos[id].append(sublista[1:])
    return dict(grupos)
def _get_gps_details_by_viagem_id(session, viagem_id):
    results = session.query(AllGpsCoordinates, PlateDetails, DadosPlacas.nome_imagem).\
        join(PlateDetails, AllGpsCoordinates.plate_details_id == PlateDetails.plate_details_id).\
        join(DadosPlacas, PlateDetails.dados_placas_id == DadosPlacas.id).\
        filter(DadosPlacas.viagem_id == viagem_id).all()
    return results
def get_gps_details_by_viagem_id(session,viagem_id):
    r = _get_gps_details_by_viagem_id(session,viagem_id)
    r = [[_[2][:-4],_[1].class_value,float(_[0].lat),float(_[0].lon)] for _ in r]
    return r
def get_row_by_img_name(relations_df,img_name):
    index = relations_df.index[relations_df.iloc[:,0] == img_name].tolist()[0]
    return index
with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
database_url = cfg['database']['url']
engine = create_engine(database_url)
#create_tables(engine)
session = sessionmaker(bind=engine)()
gps_details_full = get_gps_details_by_viagem_id(session,1)
root = cfg['paths']['root']
relations_table_name = os.path.join(root, cfg['paths']['relations_table'])
relations_df = pd.read_csv(relations_table_name, sep=',', header=None)
gps_details_full_with_id = [[get_row_by_img_name(relations_df,_[0])]+_ for _ in gps_details_full]
gps_details_full_with_id = agrupar_sublistas_por_id(gps_details_full_with_id)

print(gps_details_full_with_id)
















from geopy.distance import geodesic
def is_the_same_by_distance(gps1,gps2):
    if geodesic(gps1,gps2).meters<=18:
        return True
def get_mean_of_gps(gps1,gps2):
    mean = lambda a,b:(a+b)/2
    return mean(gps1[0],gps2[0]),mean(gps1[1],gps2[1])
def remove_duplicate_plates(dados):
    unique_plates = []
    sorted_ids = sorted(dados.keys())
    for i in range(len(sorted_ids)):
        current_id = sorted_ids[i]
        current_frame_plates = dados[current_id]
        for plate in current_frame_plates[:]:
            current_name, current_class, current_lat, current_lon = plate
            if i < len(sorted_ids) - 1:
                next_id = sorted_ids[i + 1]
                if next_id == current_id + 1:
                    next_frame_plates = dados[next_id]
                    for next_plate in next_frame_plates[:]:
                        next_name, next_class, next_lat, next_lon = next_plate
                        if next_class == current_class and is_the_same_by_distance((current_lat, current_lon), (next_lat, next_lon)):
                            avg_lat, avg_lon = get_mean_of_gps((current_lat, current_lon), (next_lat, next_lon))
                            next_plate[2], next_plate[3] = avg_lat, avg_lon
                            current_frame_plates.remove(plate)
                            break
        for remaining_plate in current_frame_plates:
            current_name, current_class, current_lat, current_lon = remaining_plate
            unique_plates.append([current_id, current_name, current_class, current_lat, current_lon])
    return unique_plates
gps_details_full_with_id = remove_duplicate_plates(gps_details_full_with_id)
print(gps_details_full_with_id)
