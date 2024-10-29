from glob import glob
import os
import subprocess
from time import sleep

# Funções reutilizadas para ler e escrever em arquivos de texto
def read_txt(path):
    data = []
    with open(path, 'r') as file:
        data = file.readlines()
        data = [y.strip() for y in data]
    return data

def write_txt(path, text):
    with open(path, 'a') as file:
        file.write(text + '\n')

# Verificar o arquivo de progresso 'done.txt'
if os.path.exists('done.txt'):
    done = read_txt('done.txt')
else:
    done = []

sleep(10)

def process_shapefiles(directory, table_name):
    shapefiles = glob(f'{directory}/*.shp')
    print(f"Verificando arquivos em: {os.path.abspath('/structures')}")
    print(f"Shapefiles no diretório {directory}: {shapefiles}")

    for shapefile in shapefiles:
        filename = os.path.basename(shapefile).replace('.shp', '')
        
        if filename not in done:
            command = f'ogr2ogr -f "PostgreSQL" PG:"host=sql port=5432 user=$POSTGRES_USER dbname=$POSTGRES_DB password=$POSTGRES_PASSWORD" -nln {table_name} -nlt POINT -t_srs EPSG:4326 {shapefile}'

            print(f'Processando: {shapefile}')
            
            result = subprocess.run(command, capture_output=True, text=True, shell=True)

            stdout = result.stdout
            stderr = result.stderr

            print("Saída padrão:")
            print(stdout)

            print("Erro padrão:")
            print(stderr)

            # Se a saída e o erro estiverem vazios, assumimos que a execução foi bem-sucedida
            if len(stdout) == 0 and len(stderr) == 0:
                print(f'Arquivo salvo: {shapefile}')
                write_txt('done.txt', filename)
    print(f'Processamento do diretório {directory} completo.')

# Processar shapefiles no diretório '/geometries' e salvar na tabela 'geometries'
process_shapefiles('/geometries', 'km_cro')
process_shapefiles('/norte', 'km_norte')
process_shapefiles('/structures', 'structures_cro')
process_shapefiles('/sul', 'km_sul')

print('Processamento finalizado.')
