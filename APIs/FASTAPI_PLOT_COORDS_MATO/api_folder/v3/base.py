from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import yaml

with open("v3/config.yml", "r") as ymlfile:
    cfg = yaml.safe_load(ymlfile)
database_url = cfg['database']['url']

engine = create_engine(database_url)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()