import os
import pandas as pd


# Folder sem a ultima barra
folder = "/mnt/teste2/Viagem3/"
import receber_nova_trip

trip_id = receber_nova_trip.main(folder)
#print(folder,trip_id)
#trip_id = 1
from utils import run as table_gps

table_gps(trip_id, 'para_norte_resultado_completo.xlsx')

from extrair_gps_timestamp import create_gps_table
#create_gps_table(os.path.join(folder,'Panoramic'),trip_id)

from encontrar_todas_placas import run as encontrar_todas_placas
#encontrar_todas_placas(os.path.join(folder,'Panoramic'),trip_id)

from get_blue_plates import main as blue_plates

#blue_plates(trip_id, folder)


from encontrar_gps_todas_placas import run as encontrar_gps_todas_placas
#encontrar_gps_todas_placas(os.path.join(folder,'images'),trip_id)

from criar_trechos import run as criar_trechos
criar_trechos(trip_id)

from classifica_vegetacao import run as classificar_vegetacao
classificar_vegetacao(trip_id)

from encontrar_todas_defensas import run as encontrar_todas_defensas
#encontrar_todas_defensas(os.path.join(folder,'Cube'),trip_id)

