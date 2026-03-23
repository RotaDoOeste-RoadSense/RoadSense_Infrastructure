import re
from tqdm.contrib.concurrent import process_map,thread_map
import json
import yaml
import os
import requests
from database_models import ImageData, AllPlatesMatched, PlateDetails
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine,asc
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm
from redis_cache_utils import cache_image
from Placas.lightglue_box_tracker_v2 import add_track_ids, TrackerConfig

Base = declarative_base()



from multiprocessing import Pool, cpu_count, Lock
global_lock = Lock()


with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)

def read_data(file_name: str) -> bytes:
    return cache_image(file_name, api_name='placas1', lock=global_lock)


def predict(file_data, classes=None):
    url = cfg['inference_sign_detection']['url']
    files = {"file": ("image.jpg", file_data, "image/jpeg")}
    data = {"classes": ','.join(map(str, classes))} if classes else {}
    error_data = ''
    for i in range(10):  # Tenta 10 vezes antes de levantar um erro
        result = requests.post(url, files=files, data=data)
        if result.status_code // 100 == 2:
            try:
                return json.loads(result.text)
            except:
                error_data += f'{result.status_code}: {result.content}\n'
        else:
            error_data += f'{result.status_code}: {result.content}\n'
    print('Requisition Error: ' + error_data)

def add_to_db(trip_id, result_data):
    result_data = {nome_imagem:placas_data for nome_imagem, placas_data in result_data.items() if placas_data}
    Session = sessionmaker(bind=engine)
    session = Session()
    results = session.query(ImageData).filter(ImageData.trip_id == trip_id,ImageData.image_name.in_(tuple(result_data.keys()))).order_by(asc(ImageData.order)).all()
    results_dict = {result.image_name:result for result in results}
    table_relation_plates_img_id = {}
    #print(result_data, results)
   
    for result in results:
        _ = AllPlatesMatched(image_id=result.image_id)
        session.add(_)
        session.commit()
        table_relation_plates_img_id[result.image_id] = _.all_plates_matched_id
    for nome_imagem, placas_data in result_data.items():
        
        for placa_data in placas_data:
            #print(placa_data)
            placa = PlateDetails(
                class_value=placa_data['class'],
                class_name=placa_data['class_name'],
                prob=placa_data['prob'],
                x1=placa_data['xyxyn'][0],
                y1=placa_data['xyxyn'][1],
                x2=placa_data['xyxyn'][2],
                y2=placa_data['xyxyn'][3],
                side=placa_data['position'],
                all_plates_matched_id = table_relation_plates_img_id[results_dict[nome_imagem].image_id],
                track_id = placa_data.get('track_id', None)
                )
            session.add(placa)
    session.commit()
    session.close()
def convert_pano2cube(imgname,cam='0'):
    return re.sub(r'_Panoramic_(\d+)',r'_Cube_\1_cam'+cam,imgname)
def process_image_data(result):
    file_path = os.path.join(result['path'], convert_pano2cube(result['image_name'],str(0)))
    data = read_data(file_path)
    prediction = predict(data, list(range(12)))
    return result['image_name'], prediction
def run(connection,path,trip_id):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    results = session.query(ImageData).filter(ImageData.trip_id == trip_id).order_by(asc(ImageData.order)).all()
    result_data = {}
    tasks = [{'path': path, 'image_name': result.image_name} for result in results]
    

    grouped = [tasks[i:i + 50] for i in range(0, len(tasks), 50)]
    results = []
    for group in tqdm(grouped, desc='Placas_detecção'):
        connection.process_data_events()
        result = thread_map(process_image_data,group, disable=True)
        results = results+result
    result_data = {_[0]:_[1] for _ in results}
    cfg_tracker = TrackerConfig(
    device="cuda",          # ou "cpu"
    pad=10.0,
    min_pair_matches=3,
    max_center_dist=None
    )
    from pathlib import Path
    missing = [fn for fn in result_data.keys() if not (Path(path)/Path(convert_pano2cube(fn))).exists()]
    print("missing:", len(missing))
    print("exemplos:", missing[:10])
    import traceback

    try:
        result_data = add_track_ids(result_data, images_dir=path, cfg=cfg_tracker, inplace=False, save_vis=True, vis_dir='saida_vis', vis_show_class_name=True)
    except Exception:
        traceback.print_exc()
        raise
    
    print(len(result_data))
    # for key in result_data:
        
    #     print(key, result_data[key])
    #add_to_db(trip_id, result_data)
if __name__=='__main__':
    run("/mnt/HD12TB/DATASET_TESTE_RONDONOPOLIS/images",4)