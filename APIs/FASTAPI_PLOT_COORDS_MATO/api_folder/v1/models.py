from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import yaml

Base = declarative_base()

class Trip(Base):
    __tablename__ = 'TRIPS'
    trip_id = Column(Integer, primary_key=True, autoincrement=True)
    root_folder = Column(String(2000))
    timestamp = Column(Integer, nullable=False)
    images = relationship("ImageData", back_populates="trip")
    
class ImageData(Base):
    __tablename__ = 'IMAGE_DATA'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_imagem = Column(String(200), nullable=False)
    latitude = Column(Numeric(18, 15), nullable=False)
    longitude = Column(Numeric(18, 15), nullable=False)
    timestamp = Column(Integer, nullable=False)
    order = Column(Integer)
    trip_id = Column(Integer, ForeignKey('TRIPS.trip_id'))
    trip = relationship("Trip", back_populates="images")


def createTables(engine):
    Base.metadata.create_all(engine)