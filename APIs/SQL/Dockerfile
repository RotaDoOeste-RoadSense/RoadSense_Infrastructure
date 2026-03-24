FROM postgis/postgis:latest

RUN apt-get update && \
    apt-get install -y gdal-bin procps


COPY ./scripts/create_tables.sql /docker-entrypoint-initdb.d/create_tables.sql



# ENV definido via docker-compose em tempo de execução
# POSTGRES_DB=mydatabase
# POSTGRES_USER=myuser
# POSTGRES_PASSWORD=mypassword
#RUN chmod +x /docker-entrypoint-initdb.d/init.sh
EXPOSE 5432
