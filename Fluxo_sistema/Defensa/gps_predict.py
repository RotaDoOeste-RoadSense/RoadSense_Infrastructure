import numpy as np
import math

class Geolocation:
    def __init__(self):
        """
        Inicializa a classe com o dicionário de conversão de pixels para metros.
        """
        self.pixels_to_meters = {
            '1792_2048': [102, 0, 2.5],
            '1472_1792': [128.0, 2.5, 5.0],
            '1353_1472': [47.6, 5.0, 7.5],
            '1281_1353': [28.8, 7.5, 10.0],
            '1240_1281': [16.4, 10.0, 12.5],
            '1210_1240': [12.0, 12.5, 15.0],
            '1188_1210': [8.8, 15.0, 17.5],
            '1171_1188': [6.8, 17.5, 20.0],
            '1159_1171': [4.8, 20.0, 22.5],
            '500_1159' : [87, 22.5, 30.0]
        }

    def get_distance(self, y):
        """
        Calcula a distância em metros a partir de uma coordenada vertical (y).

        Args:
            y (int): Coordenada y no sistema de pixels.

        Returns:
            float ou bool: Distância em metros ou False se não encontrar a região.
        """
        region = None
        for key in self.pixels_to_meters:
            inicio, fim = map(int, key.split('_'))
            if inicio <= y <= fim:
                region = key
                break

        if region is None:
            return False

        pixels_per_meter, dist_start, dist_end = self.pixels_to_meters[region]
        inicio, fim = map(int, region.split('_'))

        distancia = (np.abs(y - fim)) / pixels_per_meter + dist_start
        return distancia

    @staticmethod
    def calcular_direcao(coord1, coord2):
        """
        Calcula o azimute (direção) entre duas coordenadas geográficas.

        Args:
            coord1 (tuple): Coordenada inicial (latitude, longitude).
            coord2 (tuple): Coordenada final (latitude, longitude).

        Returns:
            float: Azimute em graus no intervalo 0-360°.
        """
        lat1, lon1, lat2, lon2 = map(math.radians, [coord1[0], coord1[1], coord2[0], coord2[1]])
        delta_lon = lon2 - lon1

        x = math.sin(delta_lon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon))
        azimute = math.atan2(x, y)
        azimute = math.degrees(azimute)

        if azimute < 0:
            azimute += 360
        return azimute

    @staticmethod
    def deslocar_coordenada(coord, azimute, distancia):
        """
        Calcula a nova coordenada geográfica após se deslocar uma certa distância em um azimute.

        Args:
            coord (tuple): Coordenada inicial (latitude, longitude).
            azimute (float): Direção em graus.
            distancia (float): Distância em metros.

        Returns:
            tuple: Nova coordenada (latitude, longitude).
        """
        lat, lon = map(math.radians, coord)
        azimute = math.radians(azimute)
        raio_terra = 6371000  # Raio da Terra em metros

        delta = distancia / raio_terra

        nova_lat = math.asin(
            math.sin(lat) * math.cos(delta) + math.cos(lat) * math.sin(delta) * math.cos(azimute)
        )
        nova_lon = lon + math.atan2(
            math.sin(azimute) * math.sin(delta) * math.cos(lat),
            math.cos(delta) - math.sin(lat) * math.sin(nova_lat)
        )

        nova_lat = math.degrees(nova_lat)
        nova_lon = math.degrees(nova_lon)
        return nova_lat, nova_lon

    def get_new_coordinate(self, coord1, coord2, y, direcao):
        """
        Obtém a nova coordenada com base na distância calculada e no azimute.

        Args:
            coord1 (tuple): Coordenada inicial (latitude, longitude).
            coord2 (tuple): Coordenada de referência (latitude, longitude).
            y (int): Coordenada vertical em pixels.

        Returns:
            tuple: Nova coordenada (latitude, longitude).
        """
        distancia = self.get_distance(y)
        if distancia is False:
            print('Y',y)
            raise ValueError("Coordenada y fora das regiões definidas.")
        azimute = self.calcular_direcao(coord1, coord2)
        if direcao == 1:
            azimute += 90
        elif direcao == 3:
            azimute -= 90
        else:
            raise ValueError("Direção inválida. Use 1 para direita ou 3 para esquerda.")
        nova_coordenada = self.deslocar_coordenada(coord2, azimute, distancia)
        return nova_coordenada


if __name__=='__main__':
    geo = Geolocation()
    coord1 = (-15.7941, -47.8825)
    coord2 = (-15.7936, -47.8820)
    y = 1500
    nova_coordenada = geo.get_new_coordinate(coord1, coord2, y, 1)
    print(f"Nova Coordenada: {nova_coordenada}")
