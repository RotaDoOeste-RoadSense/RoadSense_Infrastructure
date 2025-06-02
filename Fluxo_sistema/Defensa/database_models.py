from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Date, Integer, String, Float, ForeignKey, DECIMAL, Numeric,SmallInteger
from sqlalchemy import Index, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import DateTime, BigInteger
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
    status = Column(Integer, nullable=True)
    side = Column(String(1),nullable=True)
    all_plates_matched_id = Column(Integer)

class AllPlatesMatched(Base):
    __tablename__ = 'all_plates_matched'
    all_plates_matched_id = Column(Integer, primary_key=True)
    image_id = Column(Integer) 

class AllGpsCoordinates(Base):
    __tablename__ = 'all_gps_coordinates'
    all_gps_coordinates_id = Column(Integer, primary_key=True, autoincrement=True)
    plate_details_id = Column(Integer)
    geom = Column(Geometry(geometry_type='POINT', srid=4326))

class GuardrailDetails(Base):
    __tablename__ = 'guardrail_details'
    guardrail_details_id = Column(Integer, primary_key=True, autoincrement=True)
    class_value = Column(SmallInteger)
    class_name = Column(String(30))
    score = Column(Float)
    cam = Column(SmallInteger)
    geom = Column(Geometry(geometry_type='POINT', srid=4326))
    x1 = Column(Float, nullable=True)
    y1 = Column(Float, nullable=True)
    x2 = Column(Float, nullable=True)
    y2 = Column(Float, nullable=True)
    image_id = Column(Integer,ForeignKey('image_data.image_id'))
    outlier = Column(Boolean)
    reconstruction_error = Column(Float)

#bbox = Column(Geometry(geometry_type="POLYGON", srid=4326))
    
class MissingGuardrails(Base):
    __tablename__ = "missing_guardrails"
    guardrail_missing_id = Column(Integer, primary_key=True, autoincrement=True)
    cam = Column(SmallInteger, nullable=False)
    image_id = Column(Integer, ForeignKey("image_data.image_id"))
    class_name = Column(String(30))
    guardrail_geometry_id = Column(Integer)
    geom = Column(Geometry("POINT", 4326))


class DetectionGuardrailsAverage(Base):
    __tablename__ = "detection_guardrails_average"
    guardrail_detection_id = Column(Integer, primary_key=True, autoincrement=True)
    average = Column(Float)
    cam = Column(SmallInteger, nullable=False)
    type = Column(String(30))
    guardrail_geometry_id = Column(Integer)    


class DrenagensDatabase(Base):
    __tablename__ = 'drainage_details'
    drainage_details_id = Column(Integer, primary_key=True, autoincrement=True)
    class_value = Column(Float)
    class_name = Column(String(30))
    cam = Column(Integer, primary_key=True)
    prob = Column(Float)
    x1 = Column(Float)
    y1 = Column(Float)
    x2 = Column(Float)
    y2 = Column(Float)
    order = Column(Integer)
    unique_id = Column(Integer)
    image_id = Column(Integer)
    pred_true = Column(Float)
    latitude = Column(DECIMAL(20, 15))
    longitude = Column(DECIMAL(20, 15))

class PlacaKm(Base):
    __tablename__ = 'km_plate'
    km_plate_id = Column(Integer, primary_key=True, autoincrement=True)
    km = Column(String(20), nullable=False)
    BR = Column(String(20))
    plate_details_id = Column(Integer, ForeignKey('plate_details.plate_details_id'), nullable=False)

class ImageData(Base):
    __tablename__ = 'image_data'
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image_name = Column(String(200), nullable=False)
    latitude = Column(Numeric(15,10), nullable=False)
    longitude = Column(Numeric(15,10), nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    order = Column(BigInteger)
    trip_id = Column(Integer, nullable=False)

class HorizontalMarkings(Base):
    __tablename__ = "horizontal_markings"
    horizontal_markings_id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(SmallInteger)
    class_name = Column(String(20))
    mask_polygon = Column(Geometry(geometry_type="POLYGON", srid=4326))  # Especificando o tipo
    quality_score = Column(Float)
    image_id = Column(Integer, ForeignKey("image_data.image_id"))
    
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
    state_left = Column(Float, nullable=False)
    state_right = Column(Float, nullable=False)
    area_id = Column(Integer, nullable=False)

class Vegetacao(Base):
    __tablename__ = 'vegetation'
    vegetation_id = Column(Integer, primary_key=True, autoincrement=True)
    image_file_name_left = Column(String(200), nullable=False)
    image_file_name_right = Column(String(200), nullable=False)
    prediction_left = Column(String(20), nullable=False)
    prediction_right = Column(String(20), nullable=False)
    score_left = Column(Float, nullable=False)
    score_right = Column(Float, nullable=False)
    area_id = Column(Integer, nullable=False)
    image_id = Column(Integer)


class KM_CRO(Base):
    __tablename__ = 'km_cro'
    km_cro_id = Column(Integer, primary_key=True, autoincrement=True)
    rodovia = Column(String(80), nullable=False)
    km = Column(Float, nullable=False)
    latitude = Column(Numeric(15, 10), nullable=False)
    longitude = Column(Numeric(15, 10), nullable=False)
    km_br163 = Column(Float(precision=15), nullable=False, name='km br163')
    km_arred = Column(Float(precision=15), nullable=False, name='km arred')
    sentido = Column(String(80), nullable=False)
    geom = Column(Geometry(geometry_type='POINT', srid=4326))

class structures_cro(Base):
    __tablename__ = 'structures_cro'
    structure_cro_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    descriptio = Column(String(80), nullable=False)
    timestamp =Column(Date, nullable=False)
    begin = Column(Date, nullable=False)
    end = Column(Date, nullable=False)
    visibility = Column(Numeric(9), nullable=False)
    draworder = Column(Numeric(9), nullable=False)
    icon = Column(String(80), nullable=False)
    geom_structure = Column(Geometry(geometry_type='POINT', srid=4326))

class DefensasMetal(Base):
    __tablename__ = 'defensas_metal'

    ogc_fid = Column(Integer, primary_key=True, autoincrement=True)
    codauto = Column(Numeric(9))
    situacao = Column(Numeric(9))
    motivorepr = Column(String(80))
    data = Column(Date)
    horainicio = Column(String(80))
    horafim = Column(String(80))
    codcadastr = Column(Numeric(9))
    codmonitor = Column(String(80))
    km = Column(String(80))
    kmfinal = Column(String(80))
    sentido = Column(String(80))
    tipo = Column(String(80))
    estado = Column(String(80))
    rodovia = Column(String(80))
    lado = Column(String(80))
    altura = Column(Numeric(24, 15))
    latitude1 = Column(Numeric(24, 15))
    longitude1 = Column(Numeric(24, 15))
    latitude2 = Column(Numeric(24, 15))
    longitude2 = Column(Numeric(24, 15))
    compriment = Column(Integer)
    alturaaten = Column(String(80))
    fixacao_so = Column(String(80))
    fixacao_pa = Column(String(80))
    fixacao_po = Column(String(80))
    conservaca = Column(String(80))
    metragemfe = Column(Integer)
    conserva_1 = Column(String(80))
    metragempi = Column(Integer)
    conserva_2 = Column(String(80))
    amassadosq = Column(Integer)
    refletores = Column(String(80))
    tiporeflet = Column(String(80))
    correfleto = Column(String(80))
    observacao = Column(String(89))
    corrosao = Column(String(80))
    alinhament = Column(String(80))
    parafuso = Column(String(80))
    postemetal = Column(String(80))
    patologiap = Column(String(80))
    terminalen = Column(String(80))
    terminalsa = Column(String(80))
    elementore = Column(String(80))
    aparenciag = Column(String(80))
    status = Column(Numeric(9))
    marginal = Column(String(80))
    idandroid = Column(String(80))
    foto = Column(String(80))
    foto1 = Column(String(80))
    foto2 = Column(String(80))
    foto3 = Column(String(80))
    foto4 = Column(String(80))
    foto5 = Column(String(80))
    foto6 = Column(String(80))
    foto7 = Column(String(80))
    foto8 = Column(String(80))
    foto9 = Column(String(80))
    foto10 = Column(String(80))
    foto11 = Column(String(80))
    foto12 = Column(String(80))
    foto13 = Column(String(80))
    foto14 = Column(String(80))
    foto15 = Column(String(80))
    funcionari = Column(String(80))
    campotxt = Column(Numeric(9))
    dataenvio = Column(Date)
    codproduca = Column(String(80))
    codfunc = Column(Numeric(9))
    codfuncaud = Column(Numeric(9))
    codfuncesc = Column(String(80))
    identifica = Column(String(80))
    semestre = Column(Numeric(9))
    ano = Column(Numeric(9))
    alterarfot = Column(String(80))
    removido = Column(Numeric(9))
    codumc = Column(String(80))
    excluido = Column(String(80))
    lote = Column(String(80))
    entrega = Column(String(80))
    unnamed_8 = Column('unnamed_ 8',String(80))
    wkb_geometry = Column(Geometry('POLYGON', srid=4326))

    __table_args__ = (
        Index('defensas_metal_wkb_geometry_geom_idx', wkb_geometry, postgresql_using='gist'),
    )
    
class DefensasConcreto(Base):
    __tablename__ = 'defensas_concreto'

    ogc_fid = Column(Integer, primary_key=True, autoincrement=True)
    codauto = Column(Numeric(9))
    situacao = Column(Numeric(9))
    motivorepr = Column(String(80))
    data = Column(Date)
    horainicio = Column(String(80))
    horafim = Column(String(80))
    codcadastr = Column(Numeric(9))
    codmonitor = Column(Numeric(9))
    km = Column(String(80))
    kmfinal = Column(String(80))
    sentido = Column(String(80))
    tipo = Column(String(80))
    estado = Column(String(80))
    rodovia = Column(String(80))
    lado = Column(String(80))
    altura = Column(Numeric(24, 15))
    latitude1 = Column(Numeric(24, 15))
    longitude1 = Column(Numeric(24, 15))
    latitude2 = Column(Numeric(24, 15))
    longitude2 = Column(Numeric(24, 15))
    compriment = Column(Integer)
    alturaaten = Column(String(80))
    fixacao_so = Column(String(80))
    fixacao_pa = Column(String(80))
    fixacao_po = Column(String(80))
    refletores = Column(String(80))
    tiporeflet = Column(String(80))
    correfleto = Column(String(80))
    observacao = Column(String(80))
    situacaodr = Column(String(80))
    elementore = Column(String(80))
    armaduraex = Column(String(80))
    metragemar = Column(Integer)
    desagregac = Column(String(80))
    metragemde = Column(Integer)
    trincas = Column(String(80))
    metragemtr = Column(Integer)
    aparenciag = Column(String(80))
    status = Column(Numeric(9))
    marginal = Column(String(80))
    idandroid = Column(String(80))
    foto = Column(String(80))
    foto1 = Column(String(80))
    foto2 = Column(String(80))
    foto3 = Column(String(80))
    foto4 = Column(String(80))
    foto5 = Column(String(80))
    foto6 = Column(String(80))
    foto7 = Column(String(80))
    foto8 = Column(String(80))
    foto9 = Column(String(80))
    foto10 = Column(String(80))
    foto11 = Column(String(80))
    foto12 = Column(String(80))
    foto13 = Column(String(80))
    foto14 = Column(String(80))
    foto15 = Column(String(80))
    funcionari = Column(String(80))
    campotxt = Column(Numeric(9))
    dataenvio = Column(Date)
    codproduca = Column(String(80))
    codfunc = Column(Numeric(9))
    codfuncaud = Column(String(80))
    codfuncesc = Column(String(80))
    semestre = Column(Numeric(9))
    ano = Column(Numeric(9))
    alterarfot = Column(String(80))
    removido = Column(Numeric(9))
    codumc = Column(String(80))
    excluido = Column(String(80))
    lote = Column(String(80))
    entrega = Column(String(80))
    wkb_geometry = Column(Geometry('POLYGON', srid=4326))

    __table_args__ = (
        Index('defensas_concreto_wkb_geometry_geom_idx', wkb_geometry, postgresql_using='gist'),
    )