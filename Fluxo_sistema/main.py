import os
import pandas as pd

# Folder sem a ultima barra

folder = "/mnt/windows_share/GPS"
trip_id = 1
trip_direction = 'N' # ou 'S'

#tabela trips
import receber_nova_trip
trip_id = receber_nova_trip.main(folder, trip_direction)

# # tabela GPS
from utils import run as table_gps
table_gps(trip_id, 'GPS_norte_amostra.xlsx')

'''
from Fluxo_sistema.Placas.encontrar_todas_placas import run as encontrar_todas_placas
#encontrar_todas_placas(os.path.join(folder,'Cube'),trip_id)

from get_blue_plates import main as blue_plates
#blue_plates(trip_id, folder)

from encontrar_gps_todas_placas import run as encontrar_gps_todas_placas
#encontrar_gps_todas_placas(os.path.join(folder,'Cube'),trip_id)

from analyze_plate_quality import main as analyze_plate_quality_main
#analyze_plate_quality_main(trip_id)

from criar_trechos import run as criar_trechos
#criar_trechos(trip_id)

from classifica_vegetacao import run as classificar_vegetacao
classificar_vegetacao(trip_id)

#classificar_vegetacao(1)
#classificar_vegetacao(2)

#load some CRO elements
from load_cro import *
load_guardrails('defensas_total_2024.xlsx') 
load_drainages('DS_clean')


# predict guardrails
from encontrar_todas_defensas import run as encontrar_todas_defensas
encontrar_todas_defensas(os.path.join(folder,'Cube'),trip_id,trip_direction)
from tools_cont_els import *
adjust_pos(os.path.join(folder,'Cube'), trip_id)
'''


'''
# usar abaixo para estimar defensas unicas sem dados externos....
#from pred_defensas import run as pred_defensas
#pred_defensas(os.path.join(folder,'Cube'),trip_id,trip_direction)
#from pred_defensas import find_unique_defensas as find_unique
#find_unique(trip_id,trip_direction)
'''

#from encontrar_todas_drenagens import run as encontrar_todas_drenagens
#encontrar_todas_drenagens(os.path.join(folder,'Cube'),trip_id,trip_direction)