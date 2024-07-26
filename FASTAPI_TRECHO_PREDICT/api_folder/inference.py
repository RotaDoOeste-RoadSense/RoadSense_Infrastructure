import pandas as pd
from utils import *

# Load polylines [ID] from the CSV file
polylines_df = pd.read_csv('ID_polylines.csv')
polylines = {}
for idx, row in polylines_df.iterrows():
    coordinates = eval(row['Polyline'])
    polylines[row['ID']] = LineString([(lat, lng) for lat, lng in coordinates])

# Load polylines [Median] from the CSV file
df = pd.read_csv('canteiro_polylines.csv')
polylines_cant = {}
for index, row in df.iterrows():
    polyline = LineString(eval(row['coords']))
    polylines_cant[row['oneway']+str(row['ID'])] = polyline

# Function to find the nearest polyline and return its ID
def get_trecho(lat, lng):
    min_distance, point_min_distance, nearest_id = nearest_polyline(lat, lng, polylines)
    # ajustar nome do id
    this_id = str(nearest_id)
    final_id = ''
    if this_id.startswith('10000'):
        final_id = this_id[len(this_id)-1] + '_S'
    elif this_id.startswith('1000'):
        final_id = this_id[len(this_id)-2:] + '_S'
    else:
        final_id = this_id + '_N'

    return final_id, min_distance

def get_median(lat, lng):
    min_distance, point_min_distance, nearest_id = nearest_polyline(lat, lng, polylines_cant)
    median = 'no'
    if 'yes' in nearest_id:
        median = 'yes'
    return median
