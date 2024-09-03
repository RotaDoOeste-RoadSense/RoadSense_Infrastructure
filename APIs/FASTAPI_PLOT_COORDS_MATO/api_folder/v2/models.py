from sqlalchemy import Column, Integer, Date, Numeric, String, ForeignKey, create_engine, Float, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import yaml
from datetime import datetime

Base = declarative_base()

class Manutencao(Base):
    __tablename__ = 'maintenance'
    maintenance_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    state = Column(Float, nullable=False)
    area_id = Column(Integer, nullable=False)

class Vegetacao(Base):
    __tablename__ = 'vegetation'
    vegetation_id = Column(Integer, primary_key=True, autoincrement=True)
    image_file_name = Column(String(200), nullable=False)
    prediction = Column(String(20), nullable=False)
    score = Column(Float, nullable=False)
    area_id = Column(Integer, nullable=False)
    image_id = Column(Integer)

class ImageData(Base):
    __tablename__ = 'image_data'
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image_name = Column(String(200), nullable=False)
    latitude = Column(Float(precision=15), nullable=False)
    longitude = Column(Float(precision=15), nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    order = Column(BigInteger)
    trip_id = Column(Integer, nullable=False)

class Area(Base):
    __tablename__ = 'area'
    area_id = Column(Integer, primary_key=True, autoincrement=True)
    area_characteristics = Column(String(100), nullable=False)
    start_image_id = Column(Integer, nullable=False)
    end_image_id = Column(Integer, nullable=False)
    section_id = Column(Integer, nullable=False)

class Trip(Base):
    __tablename__ = 'trips'  
    trip_id = Column(Integer, primary_key=True, autoincrement=True)
    root_folder = Column(String(2000))
    timestamp = Column(DateTime, default=datetime.utcnow)
    way = Column(String(20))
    starting_city = Column(String(200))
    ending_city = Column(String(200))
    images = relationship("ImageData", back_populates="trip")

class Trecho(Base):
    __tablename__ = 'section'
    section_id = Column(Integer, primary_key=True, autoincrement=True)
    start_latitude_coordinates = Column(Float, nullable=False)
    start_longitude_coordinates = Column(Float, nullable=False)
    end_latitude_coordinates = Column(Float, nullable=False)
    end_longitude_coordinates = Column(Float, nullable=False)
    highway_code = Column(String(14), nullable=False)  
    section_mileage = Column(String(20), nullable=False)

def createTables(engine):
    Base.metadata.create_all(engine)