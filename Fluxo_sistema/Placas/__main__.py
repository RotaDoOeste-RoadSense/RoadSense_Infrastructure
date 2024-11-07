import os
folder = "/mnt/windows_share/GPS"
trip_id = 1
trip_direction = 'N' # ou 'S'

from encontrar_todas_placas import run as encontrar_todas_placas
encontrar_todas_placas(os.path.join(folder,'Cube'),trip_id)

from encontrar_gps_todas_placas import run as encontrar_gps_todas_placas
encontrar_gps_todas_placas(os.path.join(folder,'Cube'),trip_id)

from analyze_plate_quality import main as analyze_plate_quality_main
analyze_plate_quality_main(trip_id)

from get_blue_plates import main as blue_plates
#blue_plates(trip_id, folder)
