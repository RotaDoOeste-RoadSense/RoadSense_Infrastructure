from Vegetacao.criar_trechos import run as criar_trechos
from Vegetacao.classifica_vegetacao_cube import run as classificar_vegetacao


def run(connection,folder, trip_id, trip_direction):
    criar_trechos(connection, trip_id)
    classificar_vegetacao(connection, trip_id)
