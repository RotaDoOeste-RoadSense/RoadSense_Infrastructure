from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import yaml

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
    
class ImageData(Base):
    __tablename__ = 'image_data'
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image_name = Column(String(200), nullable=False)
    latitude = Column(Float(precision=15), nullable=False)
    longitude = Column(Float(precision=15), nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    order = Column(BigInteger)
    trip_id = Column(Integer, nullable=False)
    trip = relationship("Trip", back_populates="images")


def createTables(engine):
    Base.metadata.create_all(engine)