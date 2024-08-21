from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, create_engine, Float, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import yaml
from datetime import datetime

Base = declarative_base()

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

class ImageData(Base):
    __tablename__ = 'IMAGE_DATA'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_imagem = Column(String(200), nullable=False)
    latitude = Column(Float(precision=15), nullable=False)
    longitude = Column(Float(precision=15), nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    order = Column(BigInteger)
    trip_id = Column(Integer, nullable=False)


class Area(Base):
    __tablename__ = 'AREA'
    ID_AREA = Column(Integer,  primary_key=True, autoincrement=True)
    caracteristicas_area = Column(String(100), nullable=False)
    id_imagem_inicio = Column(Integer, nullable=False)
    id_imagem_fim = Column(Integer, nullable=False)
    ID_TRECHO = Column(Integer, nullable=False)


class trips(Base):
    __tablename__ = 'TRIPS'
    trip_id = Column(Integer,  primary_key=True, autoincrement=True)
    root_folder = Column(String(2000), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Trecho(Base):
    __tablename__ = 'TRECHO'
    ID_TRECHO = Column(Integer,  primary_key=True, autoincrement=True)
    coordenadas_latitude_inicio = Column(String(20), nullable=False)
    coordenadas_longitude_inicio = Column(String(20), nullable=False)
    coordenadas_latitude_fim = Column(String(20), nullable=False)
    coordenadas_longitude_fim = Column(String(20), nullable=False)
    codigo_rodovia = Column(String(14), nullable=False)
    quilometragem_trecho = Column(Integer, nullable=False)


def createTables(engine):
    Base.metadata.create_all(engine)