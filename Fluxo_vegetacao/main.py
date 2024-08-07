import os
import pandas as pd

# import get_desired_folder
# folder = get_desired_folder.pasta
folder = "/mnt/HD12TB/DATASET_TESTE_RONDONOPOLIS/"
import receber_nova_trip
trip_id = receber_nova_trip.main(folder)
# print(folder,trip_id)

from extrair_gps_timestamp import create_gps_table
create_gps_table(os.path.join(folder,'images'),trip_id)


from encontrar_todas_placas import run as encontrar_todas_placas
encontrar_todas_placas(os.path.join(folder,'images'),trip_id)
from encontrar_gps_todas_placas import run as encontrar_gps_todas_placas
encontrar_gps_todas_placas(os.path.join(folder,'images'),trip_id)


