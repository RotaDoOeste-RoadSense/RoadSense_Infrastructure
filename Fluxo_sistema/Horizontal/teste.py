from database_models import *
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine,asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
Base = declarative_base()
database_url = "postgresql://myuser:mypassword@127.0.0.1:5433/mydatabase"
engine = create_engine(database_url)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
trip_id = 1
r = session.query(ImageData).order_by(asc(ImageData.order)).all()
for result in r:print(result)

def create_row(id,name,polygon):
    polygon_wkt = "POLYGON((0.0 0.0, 1.0 2.0, 2.0 4.0, 0.0 3.0, 0.0 0.0))"
    novo_registro = HorizontalMarkings(
        class_id=2,
        class_name="Solid Line",
        mask_polygon=text(f"ST_GeomFromText('{polygon_wkt}')::POLYGON"),
        quality_score=0.95,
        image_id=1
    )
    session.add(novo_registro)
    session.commit()
    session.close_all()
session = Session()
r = session.query(HorizontalMarkings).all()
for result in r:print(result)

