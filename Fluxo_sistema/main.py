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

# tabela GPS
from utils import run as table_gps
table_gps(trip_id, 'GPS_norte.xlsx')
'''

'''
#from utils import mock as mock

#mock(trip_id)
from fix_coordinates import run as table_gps
#table_gps(trip_id, 'corrigido_camera_time.xlsx')


from fix_area import run as fix_area

#fix_area(trip_id, 'corrigido_camera_time.xlsx')
table_gps(trip_id, 'GPS_norte.xlsx')
'''

#from encontrar_todas_placas import run as encontrar_todas_placas
#encontrar_todas_placas(os.path.join(folder,'Panoramic'),trip_id)

#from get_blue_plates import main as blue_plates
#blue_plates(trip_id, folder)


#from encontrar_gps_todas_placas import run as encontrar_gps_todas_placas
#encontrar_gps_todas_placas(os.path.join(folder,'images'),trip_id)

#from criar_trechos import run as criar_trechos
#criar_trechos(trip_id)

#from classifica_vegetacao import run as classificar_vegetacao
#classificar_vegetacao(trip_id)


#load some CRO elements
from load_cro import *
load_guardrails('defensas_total_2024.xlsx') 
load_drainages('DS_clean')

# predict guardrails
from encontrar_todas_defensas import run as encontrar_todas_defensas
encontrar_todas_defensas(os.path.join(folder,'Cube'),trip_id,trip_direction)
#from pred_defensas import run as pred_defensas
#pred_defensas(os.path.join(folder,'Cube'),trip_id,trip_direction)
#from pred_defensas import find_unique_defensas as find_unique
#find_unique(trip_id,trip_direction)

#from encontrar_todas_drenagens import run as encontrar_todas_drenagens
#encontrar_todas_drenagens(folder,trip_id)

