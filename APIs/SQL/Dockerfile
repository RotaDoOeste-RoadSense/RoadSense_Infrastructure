FROM postgis/postgis:latest

RUN apt-get update && \
    apt-get install -y gdal-bin procps


COPY ./scripts/bruna.sql /docker-entrypoint-initdb.d/bruna.sql
COPY ./scripts/victor.sql /docker-entrypoint-initdb.d/victor.sql


# ENV definido via docker-compose em tempo de execução
# POSTGRES_DB=mydatabase
# POSTGRES_USER=myuser
# POSTGRES_PASSWORD=mypassword
#RUN chmod +x /docker-entrypoint-initdb.d/init.sh
EXPOSE 5432
