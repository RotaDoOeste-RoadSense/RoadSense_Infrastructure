from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger, ForeignKey

Base = declarative_base()

class Trips(Base):
    __tablename__ = 'TRIPS'
    trip_id = Column(Integer, primary_key=True, autoincrement=True)
    root_folder = Column(String(2000))
    timestamp = Column(String)

class ImageData(Base):
    __tablename__ = 'IMAGE_DATA'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_imagem = Column(String(200), nullable=False)
    latitude = Column(Float(precision=15), nullable=False)
    longitude = Column(Float(precision=15), nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    order = Column(BigInteger)
    trip_id = Column(Integer, ForeignKey('TRIPS.trip_id'))
    trip = relationship('Trips', back_populates='images')
Trips.images = relationship('ImageData', order_by=ImageData.id, back_populates='trip')

class AllPlatesMatched(Base):
    __tablename__ = 'all_plates_matched'
    id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(Integer, ForeignKey('IMAGE_DATA.id'))
    image = relationship('ImageData', back_populates='plates')
ImageData.plates = relationship('AllPlatesMatched', order_by=AllPlatesMatched.id, back_populates='image')

class PlateDetails(Base):
    __tablename__ = 'plate_details'
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_value = Column(Float)
    class_name = Column(String(30))
    prob = Column(Float)
    x1 = Column(Float)
    y1 = Column(Float)
    x2 = Column(Float)
    y2 = Column(Float)
    image_id = Column(Integer, ForeignKey('all_plates_matched.id'))
    plate = relationship('AllPlatesMatched', back_populates='details')
AllPlatesMatched.details = relationship('PlateDetails', order_by=PlateDetails.id, back_populates='plate')

class PlacaKm(Base):
    __tablename__ = 'placa_km'
    id_placa_km = Column(Integer, primary_key=True, autoincrement=True)
    km = Column(Integer)
    BR = Column(String(10))
    id = Column(Integer, ForeignKey('plate_details.id'))
    plate_detail = relationship('PlateDetails')

database_url = 'mysql://myuser:mypassword@sql/mydatabase'
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
