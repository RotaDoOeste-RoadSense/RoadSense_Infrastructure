FROM postgis/postgis:latest

RUN apt-get update && \
    apt-get install -y gdal-bin procps


COPY ./scripts/bruna.sql /docker-entrypoint-initdb.d/bruna.sql
COPY ./scripts/victor.sql /docker-entrypoint-initdb.d/victor.sql

# COPY init.sh /docker-entrypoint-initdb.d/init.sh
#COPY init.sh .
# COPY start.sh /start.sh

# RUN chmod +x start.sh
#COPY init.sh /docker-entrypoint-initdb.d/init.sh
# RUN chmod +x /docker-entrypoint-initdb.d/init.sh
# RUN chmod +x /docker-entrypoint-initdb.d/init.sh
#RUN chmod +x /wait.sh

ENV POSTGRES_DB=mydatabase
ENV POSTGRES_USER=myuser
ENV POSTGRES_PASSWORD=mypassword
#RUN chmod +x /docker-entrypoint-initdb.d/init.sh
EXPOSE 5432


# ENTRYPOINT ["/start.sh"]

#CMD ["postgres"]
#CMD ["sh", "-c", "sleep 10 && ogr2ogr -f \"PostgreSQL\" PG:\"host=localhost user=$POSTGRES_USER dbname=$POSTGRES_DB password=$POSTGRES_PASSWORD\" -nln km_cro -nlt POINT -t_srs EPSG:4326 /tmp/geometries.kml && tail -f /dev/null"]
#CMD ["sh", "-c", "until pg_isready -h 127.0.0.1 -p 5432 -U $POSTGRES_USER; do echo \"Waiting for postgres...\"; sleep 2; done && ogr2ogr -f \"PostgreSQL\" PG:\"host=localhost user=$POSTGRES_USER dbname=$POSTGRES_DB password=$POSTGRES_PASSWORD\" -nln km_cro -nlt POINT -t_srs EPSG:4326 /tmp/geometries.kml && tail -f /dev/null"]
# CMD ["/wait.sh", "localhost:5432", "--timeout=30", "--strict", "--", "ogr2ogr", "-f", "PostgreSQL", "PG:\"host=localhost user=$POSTGRES_USER dbname=$POSTGRES_DB password=$POSTGRES_PASSWORD\"", "-nln", "km_cro", "-nlt", "POINT", "-t_srs", "EPSG:4326", "/geometries/geometries.shp"]