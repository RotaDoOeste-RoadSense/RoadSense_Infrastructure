import os,sys,yaml
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine,asc
from sqlalchemy.orm import sessionmaker
from database_models import Trip,ImageData,DrainageDetails
with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
url_detection = cfg['inference_drainage_detection']['url']
url_classify = cfg['inference_drainage_quality']['url']
database_url = cfg['database']['url']
Base = declarative_base()
engine = create_engine(database_url)

def run(connection,folder,trip_id,*_):
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    results = session.query(ImageData).filter(ImageData.trip_id == trip_id).order_by(asc(ImageData.order)).all()
    for result in results:
        print(result)
    pass
    # encontrar_todas_placas(connection,os.path.join(folder,'Cube'),trip_id)
    # encontrar_gps_todas_placas(connection,os.path.join(folder,'Cube'),trip_id)
    # analyze_plate_quality_main(connection,trip_id)
if __name__=='__main__':
    connection = None
    folder = None
    trip_id = 1
    run(connection,folder,trip_id)
    # folder = "/mnt/windows_share/GPS"
    # trip_id = 1
    # trip_direction = 'N' # ou 'S'
    #blue_plates(trip_id, folder)
