import os,sys
from encontrar_todas_placas import run as encontrar_todas_placas
from encontrar_gps_todas_placas import run as encontrar_gps_todas_placas
from analyze_plate_quality import main as analyze_plate_quality_main
from Fluxo_sistema.Placas.old.get_blue_plates import main as blue_plates
def run(folder,trip_id):
    encontrar_todas_placas(os.path.join(folder,'Cube'),trip_id)
    encontrar_gps_todas_placas(os.path.join(folder,'Cube'),trip_id)
    analyze_plate_quality_main(trip_id)
folder = sys.argv[1]
trip_id = int(sys.argv[2])
trip_direction = sys.argv[3]
run(folder,trip_id)
