from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
import yaml

# Define the base class for SQLAlchemy models
Base = declarative_base()

# Define the GuardrailsCRO model (assuming columns: id, name, and measurement as placeholders)
class GuardrailsCRO(Base):
    __tablename__ = 'guardrails_cro'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    measurement = Column(Float)

# Connect to the database (SQLite for local use; replace with your DB URI)

with open("config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)

database_url = cfg['database']['url']
engine = create_engine(database_url)

# Create the table
Base.metadata.create_all(engine)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()

def load_guardrails(folder_path):
    # Load the Excel file into a pandas DataFrame
    df = pd.read_excel(folder_path)

    # Preview the dataframe (assumes columns 'name' and 'measurement' in the Excel file)
    print(df.head())

    # Iterate through the DataFrame and add each row to the database
    for index, row in df.iterrows():
        # Create a new GuardrailsCRO object
        new_entry = GuardrailsCRO(
            name=row['name'],
            measurement=row['measurement']
        )
        # Add the object to the session
        session.add(new_entry)

    # Commit the session to save the changes
    session.commit()

def create_intersection(infrastructure):
    # create insersection for a given structure...
