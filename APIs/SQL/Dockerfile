FROM postgis/postgis:latest

RUN apt-get update && \
    apt-get install -y gdal-bin procps


COPY ./scripts/bruna.sql /docker-entrypoint-initdb.d/bruna.sql
COPY ./scripts/victor.sql /docker-entrypoint-initdb.d/victor.sql


ENV POSTGRES_DB=mydatabase
ENV POSTGRES_USER=myuser
ENV POSTGRES_PASSWORD=mypassword
#RUN chmod +x /docker-entrypoint-initdb.d/init.sh
EXPOSE 5432
