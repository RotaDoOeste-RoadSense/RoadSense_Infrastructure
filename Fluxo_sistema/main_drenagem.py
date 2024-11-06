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
load_drainages('DS_clean')

from encontrar_todas_drenagens import run as encontrar_todas_drenagens
encontrar_todas_drenagens(os.path.join(folder,'Cube'),trip_id,trip_direction)