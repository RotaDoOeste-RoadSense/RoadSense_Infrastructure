from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DECIMAL
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

def create_tables(engine):
    Base.metadata.create_all(engine)
