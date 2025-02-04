import os,sys
from Placas.encontrar_todas_placas import run as encontrar_todas_placas
from Placas.encontrar_gps_todas_placas import run as encontrar_gps_todas_placas
from Placas.analyze_plate_quality import main as analyze_plate_quality_main
from Placas.get_blue_plates import main as blue_plates
def run(folder,trip_id):
    encontrar_todas_placas(os.path.join(folder,'Cube'),trip_id)
    encontrar_gps_todas_placas(os.path.join(folder,'Cube'),trip_id)
    analyze_plate_quality_main(trip_id)
if __name__=='__main__':
    folder = sys.argv[1]
    trip_id = int(sys.argv[2])
    trip_direction = sys.argv[3]
    run(folder,trip_id)
    # folder = "/mnt/windows_share/GPS"
    # trip_id = 1
    # trip_direction = 'N' # ou 'S'
    #blue_plates(trip_id, folder)
