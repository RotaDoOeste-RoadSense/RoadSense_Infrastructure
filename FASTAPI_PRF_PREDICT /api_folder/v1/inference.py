import pandas as pd
import numpy as np

# Função para calcular a distância haversine
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Raio da Terra em km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def check_prf_proximity(lat,lon):

        # Carregar o conjunto de dados de postos da PRF
        df_postos_PRF = pd.read_csv('FASTAPI_PRF_PREDICT /dados_dos_postos_prfs.csv', sep=';', encoding='ISO-8859-1')

        # Converter as colunas para o formato adequado
        df_postos_PRF['latitude'] = df_postos_PRF['latitude'].str.replace(',', '.', regex=False).astype(float)
        df_postos_PRF['longitude'] = df_postos_PRF['longitude'].str.replace(',', '.', regex=False).astype(float)

        # Extrair as coordenadas dos postos
        lati = df_postos_PRF['latitude']
        longi = df_postos_PRF['longitude']
        # Calcular a distância do ponto fornecido para todos os postos
        distances = haversine(lat, lon, lati, longi)
        
        # Verificar se existe um posto da PRF a menos de 10 km
        proximity_limit = 0.10  # Limite de proximidade em km
        is_near = np.any(distances < proximity_limit)
        
        return is_near

