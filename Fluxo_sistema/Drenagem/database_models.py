from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Date, Integer, String, Float, ForeignKey, DECIMAL, Numeric
from sqlalchemy import DateTime, BigInteger, SmallInteger
from datetime import datetime
from geoalchemy2 import Geometry

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
    latitude = Column(Numeric(15,10), nullable=False)
    longitude = Column(Numeric(15,10), nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    order = Column(BigInteger)
    trip_id = Column(Integer, nullable=False)

class DrainageDetails(Base):
    __tablename__ = 'drainage_details'
    drainage_details_id = Column(Integer, primary_key=True, autoincrement=True)
    x1 = Column(Float)
    y1 = Column(Float)
    x2 = Column(Float)
    y2 = Column(Float)
    cam = Column(SmallInteger)
    quality_value = Column(SmallInteger)
    geom = Column(Geometry(geometry_type='POINT', srid=4326))
    image_id = Column(Integer, nullable=False)