# Folder sem a ultima barra
folder = "/mnt/hd1/Extracoes/SP_2024_sul"
#trip_id = 2
trip_direction = 'S' # ou 'S'

#tabela trips
import receber_nova_trip
trip_id = receber_nova_trip.main(folder, trip_direction)

# # tabela GPS
from utils import run as table_gps
table_gps(trip_id, 'trips/SP_sul.xlsx')