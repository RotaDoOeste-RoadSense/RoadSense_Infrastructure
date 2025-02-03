import os
folder = "/mnt/windows_share/GPS"
#folder = "/mnt/hd1/Extracoes/SP_2024_sul"
trip_id = 1


from criar_trechos import run as criar_trechos
#criar_trechos(trip_id)

from classifica_vegetacao_cube import run as classificar_vegetacao
classificar_vegetacao(trip_id)