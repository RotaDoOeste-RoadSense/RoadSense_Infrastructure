from sqlalchemy import create_engine, Column, Integer, String, Float, text, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, select
from geoalchemy2 import Geometry
from geoalchemy2 import WKTElement
import pandas as pd
import yaml
import logging
from sqlalchemy.exc import SQLAlchemyError
import os

def load_guardrails(folder_path):
    # Connect to the database (SQLite for local use; replace with your DB URI)
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)


    database_url = cfg['database']['url']
    engine = create_engine(database_url)

    # Create a metadata instance
    metadata = MetaData()
    guardrails_cro = Table('guardrails_cro', metadata, autoload_with=engine)

    # Create the table
    #this_base.metadata.create_all(engine)

    # Create a session to interact with the database
    Session = sessionmaker(bind=engine)
    session = Session()

    # Corrected row count query
    stmt = select(func.count()).select_from(guardrails_cro)
    row_count = session.execute(stmt).scalar()
    
    if row_count > 0:
        print(f"guardrails_cro already populated with {row_count} records. Skipping data insertion.")
        return  # Exit the function if table is already populated

    print("Populating table guardrails_cro...")

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
        df = pd.read_excel(folder_path, sheet_name=sheet)
        comprimento_col = 'Comprimento' if 'Comprimento' in df.columns else 'comprimento'

        # Iterate through the DataFrame and add each row to the database
        for index, row in df.iterrows():
            linestring = f"LINESTRING({row['Longitude1']} {row['Latitude1']}, {row['Longitude2']} {row['Latitude2']})"

            if (row['Longitude1'], row['Latitude1']) == (0, 0) or (row['Longitude2'], row['Latitude2']) == (0, 0):
                print(f"Skipping entry with LINESTRING containing (0, 0): {linestring}")
                continue

            # Prepare the dictionary with the data to insert
            new_entry = {
                'km': row['km'],
                'km_final': row['kmFinal'],
                'sentido': row['sentido'],
                'tipo': row['tipo'],
                'altura': row['altura'],
                'comprimento': row.get(comprimento_col, None),
                'lado': row['lado'],
                'geom': WKTElement(linestring, srid=4326)
            }

            # Insert the row into the database using core insert
            stmt = guardrails_cro.insert().values(new_entry)
            session.execute(stmt)

    # Commit the session to save the changes
    session.commit()

def load_drainages(folder_path):
    # Connect to the database (SQLite for local use; replace with your DB URI)
    with open("config.yml", "r") as ymlfile:
        cfg = yaml.safe_load(ymlfile)


    database_url = cfg['database']['url']
    engine = create_engine(database_url)

    # Create a metadata instance
    metadata = MetaData()
    drainages_cro = Table('drainages_cro', metadata, autoload_with=engine)

    # Create the table
    #this_base.metadata.create_all(engine)

    # Create a session to interact with the database
    Session = sessionmaker(bind=engine)
    session = Session()

    # Corrected row count query
    stmt = select(func.count()).select_from(drainages_cro)
    row_count = session.execute(stmt).scalar()
    
    if row_count > 0:
        print(f"drainages_cro already populated with {row_count} records. Skipping data insertion.")
        return  # Exit the function if table is already populated

    print("Populating table drainages_cro...")

    # Load the Excel file into a pandas DataFrame
    # File to exclude
    exclude_file = 'filtered_RotaDoOeste_DrenagemSuperficial_Removidos.xlsx'

    # List all .xlsx files in the directory, excluding the specified one
    xlsx_files = [f for f in os.listdir(folder_path) if f.endswith('.xlsx') and f != exclude_file]

    # Read each .xlsx file into a Pandas DataFrame
    for file in xlsx_files:
        file_path = os.path.join(folder_path, file)
        df = pd.read_excel(file_path)

        comprimento_col = 'Comprimento' if 'Comprimento' in df.columns else 'comprimento'
        #km_final_col = 'KmFinal' if 'KmFinal' in df.columns else 'kmFinal'

        # Iterate through the DataFrame and add each row to the database
        for index, row in df.iterrows():
            linestring = f"LINESTRING({row['Longitude1']} {row['Latitude1']}, {row['Longitude2']} {row['Latitude2']})"

            if (row['Longitude1'], row['Latitude1']) == (0, 0) or (row['Longitude2'], row['Latitude2']) == (0, 0):
                print(f"Skipping entry with LINESTRING containing (0, 0): {linestring}")
                continue

            # Prepare the dictionary with the data to insert
            new_entry = {
                'km': row['km'],
                'km_final': row['KmFinal'],
                'sentido': row['Sentido'],
                'tipo': row['Tipo'],
                'altura': row['Altura'],
                'comprimento': row.get(comprimento_col, None),
                'geom': WKTElement(linestring, srid=4326)
            }

            # Insert the row into the database using core insert
            stmt = drainages_cro.insert().values(new_entry)
            session.execute(stmt)

    # Commit the session to save the changes
    session.commit()