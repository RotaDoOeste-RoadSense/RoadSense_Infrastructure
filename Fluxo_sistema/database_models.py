from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DECIMAL
from sqlalchemy import DateTime, BigInteger
from datetime import datetime

Base = declarative_base()

class PlacaDatabase(Base):
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

class DadosPlacas(Base):
    __tablename__ = 'all_plates_matched'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_imagem = Column(String(255))
    viagem_id = Column(Integer)
    placas = relationship("PlacaDatabase", backref="all_plates_matched")

class AllGpsCoordinates(Base):
    __tablename__ = 'all_gps_coordinates'
    id = Column(Integer, primary_key=True, autoincrement=True)
    plate_details_id = Column(Integer, ForeignKey('plate_details.id'))
    lat = Column(DECIMAL(20, 15))
    lon = Column(DECIMAL(20, 15))
    plate = relationship("PlacaDatabase", backref="all_gps_coordinates")

class DefensasDatabase(Base):
    __tablename__ = 'guardrail_details'
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_value = Column(Float)
    class_name = Column(String(30))
    cam = Column(Integer, primary_key=True)
    prob = Column(Float)
    x1 = Column(Float)
    y1 = Column(Float)
    x2 = Column(Float)
    y2 = Column(Float)
    image_id = Column(Integer, ForeignKey('all_guardrails_matched.id'))

class DadosDefensas(Base):
    __tablename__ = 'all_guardrails_matched'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_imagem = Column(String(255))
    viagem_id = Column(Integer)
    defensas = relationship("DefensasDatabase", backref="all_guardrails_matched")


class ImageData(Base):
    __tablename__ = 'IMAGE_DATA'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_imagem = Column(String(200), nullable=False)
    latitude = Column(Float(precision=15), nullable=False)
    longitude = Column(Float(precision=15), nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    order = Column(BigInteger)
    trip_id = Column(Integer, nullable=False)


class Trecho(Base):
    __tablename__ = 'TRECHO'
    ID_TRECHO = Column(Integer,  primary_key=True, autoincrement=True)
    coordenadas_latitude_inicio = Column(String(20), nullable=False)
    coordenadas_longitude_inicio = Column(String(20), nullable=False)
    coordenadas_latitude_fim = Column(String(20), nullable=False)
    coordenadas_longitude_fim = Column(String(20), nullable=False)
    codigo_rodovia = Column(String(14), nullable=False)
    quilometragem_trecho = Column(Integer, nullable=False)
   
class Area(Base):
    __tablename__ = 'AREA'
    ID_AREA = Column(Integer,  primary_key=True, autoincrement=True)
    caracteristicas_area = Column(String(100), nullable=False)
    id_imagem_inicio = Column(Integer, nullable=False)
    id_imagem_fim = Column(Integer, nullable=False)
    ID_TRECHO = Column(Integer, nullable=False)

class Estrutura(Base):
    __tablename__ = 'ESTRUTURA'
    ID_ESTRUTURA = Column(Integer,  primary_key=True, autoincrement=True)
    descricao_tipo_estrutura = Column(String(100), nullable=False)
    ID_TRECHO = Column(Integer, nullable=False)

class Manutencao(Base):
    __tablename__ = 'MANUTENCAO'
    ID_MANUTENCAO = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(DateTime, nullable = False, default=datetime.utcnow)
    situacao = Column(Float(precision=15), nullable=False)
    ID_AREA = Column(Integer, nullable=False)


class Vegetacao(Base):
    __tablename__ = 'VEGETACAO'
    ID_VEGETACAO = Column(Integer, primary_key=True, autoincrement=True)
    nome_arquivo_imagem = Column(String(20), nullable=False)
    classificacao = Column(String(20), nullable=False)
    score = Column(Float(precision=15), nullable=False)
    ID_AREA = Column(Integer, nullable=False)
    ID_IMAGE_DATA = Column(Integer, nullable=False)


class Trips(Base):
    __tablename__ = 'TRIPS'
    trip_id = Column(Integer,  primary_key=True, autoincrement=True)
    root_folder = Column(String(2000), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

def create_tables(engine):
    Base.metadata.create_all(engine)
