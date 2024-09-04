from datetime import datetime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import create_engine, DateTime, Column, Integer, String, Float, BigInteger, ForeignKey

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
    trip_id = Column(Integer, nullable=False)

class AllPlatesMatched(Base):
    __tablename__ = 'all_plates_matched'
    all_plates_matched_id = Column(Integer, primary_key=True)
    image_id = Column(Integer)
   

class PlateDetails(Base):
    __tablename__ = 'plate_details'
    plate_details_id = Column(Integer, primary_key=True)
    class_value = Column(Float, nullable=True)
    class_name = Column(String(30), nullable=True)
    prob = Column(Float, nullable=True)
    x1 = Column(Float, nullable=True)
    y1 = Column(Float, nullable=True)
    x2 = Column(Float, nullable=True)
    y2 = Column(Float, nullable=True)
    all_plates_matched_id = Column(Integer)

class PlacaKm(Base):
    __tablename__ = 'km_plate'
    km_plate_id= Column(Integer, primary_key=True, autoincrement=True)
    km = Column(Integer)
    BR = Column(String(10))
    plate_details_id = Column(Integer)

database_url = 'postgresql://myuser:mypassword@127.0.0.1:5433/mydatabase'
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
