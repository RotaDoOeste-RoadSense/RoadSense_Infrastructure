#FROM python:3.9.20-slim-bullseye

FROM postgis/postgis:latest

RUN apt-get update && \
    apt-get install -y gdal-bin procps

COPY geometries/ /geometries

COPY norte/ /norte

COPY structures/ /structures

COPY sul/ /sul

COPY concreto/ /concreto

COPY metal/ /metal

COPY insert_geometries.py /workspace/

WORKDIR /workspace

ENV POSTGRES_DB=mydatabase
ENV POSTGRES_USER=myuser
ENV POSTGRES_PASSWORD=mypassword

CMD [ "python3" , "insert_geometries.py"]