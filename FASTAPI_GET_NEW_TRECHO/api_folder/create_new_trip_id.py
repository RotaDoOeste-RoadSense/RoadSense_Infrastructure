from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, DateTime, ForeignKey,BigInteger,String,Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import yaml
Base = declarative_base()

class Trip(Base):
    __tablename__ = 'TRIPS'  
    trip_id = Column(Integer, primary_key=True, autoincrement=True)
    root_folder = Column(String(2000))
    timestamp = Column(DateTime, default=datetime.utcnow)
    images = relationship("ImageData", back_populates="trip")
class ImageData(Base):
    __tablename__ = 'IMAGE_DATA'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_imagem = Column(String(200), nullable=False)
    latitude = Column(Numeric(18, 15), nullable=False)
    longitude = Column(Numeric(18, 15), nullable=False)
    timestamp = Column(Integer, nullable=False)
    order = Column(BigInteger)
    trip_id = Column(Integer, ForeignKey('TRIPS.trip_id'))
    trip = relationship("Trip", back_populates="images")
def create_tables(engine):
    Base.metadata.create_all(engine)
def create_new_trip(root_folder):
    Base = declarative_base()
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)
    database_url = cfg['database']['url']
    engine = create_engine(database_url)
    create_tables(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    new_trip = Trip(root_folder=root_folder)
    session.add(new_trip)
    session.commit()
    trip_id = new_trip.trip_id
    return trip_id