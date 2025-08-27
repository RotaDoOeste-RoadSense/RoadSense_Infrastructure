from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, DateTime, ForeignKey,BigInteger,String,Numeric,Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import yaml
Base = declarative_base()

class Trip(Base):
    __tablename__ = 'trips'  
    trip_id = Column(Integer, primary_key=True, autoincrement=True)
    root_folder = Column(String(2000))
    timestamp = Column(DateTime, default=datetime.utcnow)
    way = Column(String(20))
    starting_city = Column(String(200))
    ending_city = Column(String(200))
    
class ImageData(Base):
    __tablename__ = 'image_data'
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image_name = Column(String(200), nullable=False)
    latitude = Column(Float(precision=15), nullable=False)
    longitude = Column(Float(precision=15), nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    order = Column(BigInteger)
    trip_id = Column(Integer)
    
def create_tables(engine):
    Base.metadata.create_all(engine)

def create_new_trip(root_folder, way, starting_city, ending_city, production=False):
    Base = declarative_base()
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    database_url = cfg['database']['url']
    if production:
        database_url = cfg['database']['url_production']
      
    engine = create_engine(database_url)
    create_tables(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    new_trip = Trip(
        root_folder=root_folder,
        way=way,
        starting_city=starting_city,
        ending_city=ending_city
    )
    session.add(new_trip)
    session.commit()
    response_content = {
        'trip_id' : new_trip.trip_id,
        'root_folder' : new_trip.root_folder,
        'timestamp' : str(new_trip.timestamp),
        'way' : new_trip.way,
        'starting_city' : new_trip.starting_city,
        'ending_city' : new_trip.ending_city
    }
    session.close()
    return response_content