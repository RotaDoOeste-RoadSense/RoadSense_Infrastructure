from glob import glob 
import os
import subprocess
from time import sleep

shapefiles = glob('/geometries/*.shp')
print(shapefiles)

def read_txt(path):
    data = []
    with open (path, 'r') as file:
        data = file.readlines()
        data = [y.strip() for y in data]
    return data


def write_txt(path, text):

    with open(path, 'w') as file:

        file.write(text + '\n')

if os.path.exists('done.txt'):
    done = read_txt('done.txt')
else:
    done = []

sleep(10)

for shapefile in shapefiles:
    filename = os.path.basename(shapefile)
    filename = filename.replace('.shp','')
    if filename not in done:    
        command = f'ogr2ogr -f "PostgreSQL" PG:"host=sql port=5432 user=$POSTGRES_USER dbname=$POSTGRES_DB password=$POSTGRES_PASSWORD" -nln {filename} -nlt POINT -t_srs EPSG:4326 {shapefile}'
        
        print(shapefiles)
         
        result = subprocess.run(command, capture_output=True, text=True, shell=True)

        # Captura a saída padrão (stdout) e o erro padrão (stderr)
        stdout = result.stdout
        stderr = result.stderr

        print("Saída padrão:")
        print(stdout)

        print("Erro padrão:")
        print(stderr)

        if len(stdout) == 0 and len(stderr) == 0:
            print('arquivo_salvo')
            write_txt('done.txt', filename)

