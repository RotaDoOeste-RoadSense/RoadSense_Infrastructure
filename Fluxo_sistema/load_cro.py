from sqlalchemy import create_engine, Column, Integer, String, Float, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from geoalchemy2 import Geometry
from geoalchemy2 import WKTElement
import pandas as pd
import yaml
import logging
from sqlalchemy.exc import SQLAlchemyError

# Define the GuardrailsCRO model 
this_base = declarative_base()
class GuardrailsCRO(this_base):
    __tablename__ = 'guardrails_cro'
    id = Column(Integer, primary_key=True, autoincrement=True) # não usar codAuto, deixar autoincrement....
    km = Column(String)
    km_final = Column(String)
    sentido = Column(String)
    tipo = Column(String)
    altura = Column(Float)
    comprimento = Column(Float)
    lado = Column(String)
    geom = Column(Geometry(geometry_type='LINESTRING', srid=4326))  # WGS 84 (srid 4326) for latitude/longitude

def load_guardrails(folder_path):
    # Connect to the database (SQLite for local use; replace with your DB URI)
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    database_url = cfg['database']['url']
    engine = create_engine(database_url)

    # Create the table
    this_base.metadata.create_all(engine)

    # Create a session to interact with the database
    Session = sessionmaker(bind=engine)
    session = Session()

    # Load the Excel file into a pandas DataFrame
    df = pd.read_excel(folder_path)

    sheet_names = [
        "Barreira Concreto",
        "Defensa Metalica",
        "Defensa OAE", 
        "Tela Antiofuscante"
    ]

    # Iterate through each sheet
    for sheet in sheet_names:
        # Load the specific sheet into a pandas DataFrame
        df = pd.read_excel(folder_path, sheet_name=sheet)
        # Ensure both "Comprimento" and "comprimento" are considered
        comprimento_col = 'Comprimento' if 'Comprimento' in df.columns else 'comprimento'

        # Iterate through the DataFrame and add each row to the database
        for index, row in df.iterrows():
            # Create the LINESTRING using the lat/lon pairs (WKT format: "LINESTRING(lon1 lat1, lon2 lat2)")
            linestring = f"LINESTRING({row['Longitude1']} {row['Latitude1']}, {row['Longitude2']} {row['Latitude2']})"
            
            # Create a new GuardrailsCRO object
            new_entry = GuardrailsCRO(
                km=row['km'],
                km_final=row['kmFinal'],
                sentido=row['sentido'],
                tipo=row['tipo'],
                altura=row['altura'],
                comprimento=row.get(comprimento_col, None),  # Use .get() to handle missing keys gracefully
                lado=row['lado'],
                geom=WKTElement(linestring, srid=4326)  # Create WKTElement for PostGIS
            )

            # Add the object to the session
            session.add(new_entry)

    # Commit the session to save the changes
    session.commit()

# create intersection with sentido, tipo, lado as attributes
def create_intersections_guardrails():
    # Connect to the database (SQLite for local use; replace with your DB URI)
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    database_url = cfg['database']['url']
    try:
        engine = create_engine(database_url)
    except SQLAlchemyError as e:
        print(f"Error creating engine: {e}")

    # Define the SQL for creating the image_data_with_geom view
    create_image_data_with_geom_view = text("""
        CREATE OR REPLACE VIEW public.image_data_with_geom AS 
        SELECT image_id,
            image_name,
            timestamp,
            "order",  -- Use double quotes to escape the column name
            trip_id,
            ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) AS geom
        FROM image_data;
    """)

    # Define the SQL for creating the view `dev_guardrails_evelop`
    create_dev_guardrails_evelop_view = text("""
        CREATE OR REPLACE VIEW public.guardrails_cro_evelop
        AS SELECT row_number() OVER () AS rnum,
            id,
            st_setsrid(st_buffer(geom, 0.00015::double precision), 4326) AS geom,
            sentido,
            tipo,
            lado
        FROM guardrails_cro dg;
    """)

    # Execute the SQL commands using text() wrapper
    try:
        with engine.connect() as connection:
            connection.execute(create_image_data_with_geom_view)
            connection.commit()
    except SQLAlchemyError as e:
        print(f"Error executing the image geom query: {e}")

    try:
        with engine.connect().execution_options(autocommit=True) as connection:
            connection.execute(create_dev_guardrails_evelop_view)
            connection.commit()
    except SQLAlchemyError as e:
        print(f"Error executing the guardrails_evelop query: {e}")
