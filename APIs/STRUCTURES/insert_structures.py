from glob import glob
import os
import subprocess
from time import sleep

# Obtenha todos os arquivos .shp no diretório especificado
shapefiles = glob('/structures/*.shp')
print(shapefiles)

def read_txt(path):
    data = []
    with open(path, 'r') as file:
        data = file.readlines()
        data = [y.strip() for y in data]
    return data

def write_txt(path, text):
    with open(path, 'a') as file:
        file.write(text + '\n')

if os.path.exists('done.txt'):
    done = read_txt('done.txt')
else:
    done = []

sleep(10)

# Nome da tabela unificada
unified_table_name = 'structures_cro'

for shapefile in shapefiles:
    filename = os.path.basename(shapefile).replace('.shp', '')

    if filename not in done:
        # Comando para converter geometria para Point
        #command = f'ogr2ogr -f "PostgreSQL" PG:"host=sql port=5432 user=$POSTGRES_USER dbname=$POSTGRES_DB password=$POSTGRES_PASSWORD" -append -nln {unified_table_name} -sql "SELECT ST_Centroid(geom) as geom, name FROM {filename}" {shapefile}'
        #command = f'ogr2ogr -f "PostgreSQL" PG:"host=sql port=5432 user=$POSTGRES_USER dbname=$POSTGRES_DB password=$POSTGRES_PASSWORD" -append -nln {unified_table_name} -skipfailures {shapefile}'
        command = f'ogr2ogr -f "PostgreSQL" PG:"host=sql port=5432 user=$POSTGRES_USER dbname=$POSTGRES_DB password=$POSTGRES_PASSWORD" -nln {unified_table_name} -nlt POINT -t_srs EPSG:4326 {shapefile}'

        print(f'Processando: {shapefile}')
         
        result = subprocess.run(command, capture_output=True, text=True, shell=True)

        stdout = result.stdout
        stderr = result.stderr

        print("Saída padrão:")
        print(stdout)

        print("Erro padrão:")
        print(stderr)

        if len(stdout) == 0 and len(stderr) == 0:
            print(f'Arquivo salvo: {shapefile}')
            write_txt('done.txt', filename)

print('Processamento completo.')
