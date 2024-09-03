from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Date, Integer, String, Float, ForeignKey, DECIMAL
from sqlalchemy import DateTime, BigInteger
from datetime import datetime

Base = declarative_base()


class Trip(Base):
    __tablename__ = 'trips'  
    trip_id = Column(Integer, primary_key=True, autoincrement=True)
    root_folder = Column(String(2000))
    timestamp = Column(DateTime, default=datetime.utcnow)
    way = Column(String(20))
    starting_city = Column(String(200))
    ending_city = Column(String(200))
    images = relationship("ImageData", back_populates="trip")

#FAZER A MUDANÇA DE ONDE ESTIVER PLACA DATABASE
# class PlacaDatabase(Base):
#     __tablename__ = 'plate_details'
#     plate_details_id = Column(Integer, primary_key=True, autoincrement=True)
#     class_value = Column(Float)
#     class_name = Column(String(30))
#     prob = Column(Float)
#     x1 = Column(Float)
#     y1 = Column(Float)
#     x2 = Column(Float)
#     y2 = Column(Float)
#     image_id = Column(Integer, ForeignKey('all_plates_matched.id'))
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
    image_id = Column(Integer, ForeignKey('all_plates_matched.id'), nullable=True)
    plate = relationship("AllPlatesMatched", back_populates="details")



# FAZER A MUDANÇA DE ONDE ESTIVER DADOS PLACAS
# class DadosPlacas(Base):
#     __tablename__ = 'all_plates_matched'
#     all_plates_matched_id = Column(Integer, primary_key=True, autoincrement=True)
#     nome_imagem = Column(String(255))
#     viagem_id = Column(Integer)
#     placas = relationship("PlacaDatabase", backref="all_plates_matched")

class AllPlatesMatched(Base):
    __tablename__ = 'all_plates_matched'
    all_plates_matched_id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey('image_data.id'), nullable=True)
    image = relationship("ImageData", back_populates="plates")


class AllGpsCoordinates(Base):
    __tablename__ = 'all_gps_coordinates'
    all_gps_coordinates_id = Column(Integer, primary_key=True, autoincrement=True)
    plate_details_id = Column(Integer, ForeignKey('plate_details.id'))
    lat = Column(DECIMAL(20, 15))
    lon = Column(DECIMAL(20, 15))
    plate = relationship("AllPlatesMatched", backref="all_gps_coordinates")

class DefensasDatabase(Base):
    __tablename__ = 'guardrail_details'
    guardrail_details_id = Column(Integer, primary_key=True, autoincrement=True)
    class_value = Column(Float)
    class_name = Column(String(30))
    cam = Column(Integer, primary_key=True)
    prob = Column(Float)
    x1 = Column(Float)
    y1 = Column(Float)
    x2 = Column(Float)
    y2 = Column(Float)
    image_id = Column(Integer, ForeignKey('all_guardrails_matched.id'))


class AllDefensasMatched(Base):
    __tablename__ = 'all_guardrail_matched'
    all_guardrail_matched_id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(Integer, nullable=False)


class PlacaKm(Base):
    __tablename__ = 'km_plate'
    km_plate_id = Column(Integer, primary_key=True, autoincrement=True)
    km = Column(String(20), nullable=False)
    BR = Column(String(20))
    plate_details_id = Column(Integer, ForeignKey('plate_details.plate_details_id'), nullable=False)
    plate_detail = relationship('PlateDetails')

class ImageData(Base):
    __tablename__ = 'image_data'
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image_name = Column(String(200), nullable=False)
    latitude = Column(Float(precision=15), nullable=False)
    longitude = Column(Float(precision=15), nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    order = Column(BigInteger)
    trip_id = Column(Integer, nullable=False)

class Trecho(Base):
    __tablename__ = 'section'
    section_id = Column(Integer, primary_key=True, autoincrement=True)
    start_latitude_coordinates = Column(Float, nullable=False)
    start_longitude_coordinates = Column(Float, nullable=False)
    end_latitude_coordinates = Column(Float, nullable=False)
    end_longitude_coordinates = Column(Float, nullable=False)
    highway_code = Column(String(14), nullable=False)  
    section_mileage = Column(String(20), nullable=False)
   
class Area(Base):
    __tablename__ = 'area'
    area_id = Column(Integer, primary_key=True, autoincrement=True)
    area_characteristics = Column(String(100), nullable=False)
    start_image_id = Column(Integer, nullable=False)
    end_image_id = Column(Integer, nullable=False)
    section_id = Column(Integer, nullable=False)

class Estrutura(Base):
    __tablename__ = 'structure'
    structure_id = Column(Integer, primary_key=True, autoincrement=True)
    structure_type_description = Column(String(100), nullable=False)
    section_id = Column(Integer, nullable=False)

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
