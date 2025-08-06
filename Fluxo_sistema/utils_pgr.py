
from glob import glob
import os


def generate_pgr_sh(input_folder, output_folder):
    pgrs = glob(input_folder + '/*.pgr')
    pgrs = sorted(filter(lambda _:_.endswith('000000.pgr'),pgrs))
    lines = []
    for pgr in pgrs:
        lines.append(f"LadybugCubeMap '{pgr}' '{output_folder}/' 2048")
        



print(generate_pgr_sh('/home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema/', '/home/servidor/VICTOR/RoadSense_Infrastructure/Fluxo_sistema/cube'))