import os
import pandas as pd

# Folder sem a ultima barra

folder = "/mnt/teste/GPS_norte_from43"
trip_id = 1
trip_direction = 'NORTE' # ou 'SUL'

'''
#tabela trips
import receber_nova_trip
trip_id = receber_nova_trip.main(folder)

# # tabela GPS
from utils import run as table_gps
table_gps(trip_id, 'GPS_norte.xlsx')
'''

#load some CRO elements
from load_cro import *
load_guardrails('defensas_total_2024.xlsx') 


# predict guardrails
from encontrar_todas_defensas import run as encontrar_todas_defensas
encontrar_todas_defensas(os.path.join(folder,'Cube'),trip_id,trip_direction)
#from tools_cont_els import *
#adjust_pos(os.path.join(folder,'Cube'), trip_id)

'''
# usar abaixo para estimar defensas unicas sem dados externos....
#from pred_defensas import run as pred_defensas
#pred_defensas(os.path.join(folder,'Cube'),trip_id,trip_direction)
#from pred_defensas import find_unique_defensas as find_unique
#find_unique(trip_id,trip_direction)
'''