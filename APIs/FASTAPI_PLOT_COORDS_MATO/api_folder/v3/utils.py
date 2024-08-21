import folium
import numpy as np
import re

def deslocaPontos(pontos, offset, lado):
    deslocados = []
    if len(pontos) < 2:
        raise ValueError("passe ao menos dois pontos.")
    
    normal = np.array([0, 0])

    for i in range(len(pontos) - 1):
        p1 = np.array(pontos[i])
        p2 = np.array(pontos[i + 1])
        direcao = p2 - p1
        norma_direcao = np.linalg.norm(direcao)
        if norma_direcao != 0:
            direcao_normalizada = direcao / norma_direcao
            normal = np.array([-direcao_normalizada[1], direcao_normalizada[0]])  # Rotação de 90 graus para obter o vetor normal
        
        if lado == 'esquerda':
            normal = -normal
        
        deslocamento = normal * offset
        deslocados.append(tuple(p1 + deslocamento))
    
    ultimoP = np.array(pontos[-1])
    deslocamentoFin = normal * offset
    deslocados.append(tuple(ultimoP + deslocamentoFin))
    
    return deslocados

def convert_pano_cube(pano_img_name,cam):
    return re.sub(r'Panoramic_(\d{6})',f'Cube_\\1_'+cam,pano_img_name)

def geraMapa(lats, longs, intensiMato, lados, popups, nomeArq='v3/mapa.html'):
    cores = {'baixo': 'green', 'medio': 'yellow', 'grande': 'red'}
    distancia_offsetEsquerda =  0.0002
    distancia_offsetDireta = 0.00008
    intensiMato = [float(str(value).replace(',', '.')) for value in intensiMato]
    coordenadas = list(zip(lats, longs))
    larguraLinha = 7
    latitude_media = sum(lats) / len(lats)
    longitude_media = sum(longs) / len(longs)
    lados = list(lados)
    mapa = folium.Map(location=[latitude_media, longitude_media], zoom_start=12)
    
    for i in range(1, len(coordenadas)):
        pontoAnterior = coordenadas[i - 1]
        pontoAtual = coordenadas[i]
    
        if intensiMato[i] < 0.33:
            cor = cores['baixo']
        elif intensiMato[i] < 0.66:
            cor = cores['medio']
        else:
            cor = cores['grande']
        
        if lados[i] == 'ambos':
            pontoDeslocadoDireita = deslocaPontos([pontoAnterior, pontoAtual], distancia_offsetDireta, 'direita')
            pontoDeslocadoEsquerda = deslocaPontos([pontoAnterior, pontoAtual], distancia_offsetEsquerda, 'esquerda')
            folium.PolyLine(locations=pontoDeslocadoDireita, color=cor, weight=larguraLinha).add_to(mapa)
            folium.PolyLine(locations=pontoDeslocadoEsquerda, color=cor, weight=larguraLinha).add_to(mapa)
        elif lados[i]=='direita':
            pontoDeslocado = deslocaPontos([pontoAnterior, pontoAtual], distancia_offsetDireta, lados[i])
            folium.PolyLine(locations=pontoDeslocado, color=cor, weight=larguraLinha, popup=folium.Popup(popups[i], max_width=300)).add_to(mapa)
        else:
            
            pontoDeslocado = deslocaPontos([pontoAnterior, pontoAtual], distancia_offsetEsquerda, lados[i])
            folium.PolyLine(locations=pontoDeslocado, color=cor, weight=larguraLinha).add_to(mapa)
            
    #folium.Marker(location=coordenadas[0], popup='Ponto Inicial', icon=folium.Icon(color='red')).add_to(mapa)
    #folium.Marker(location=coordenadas[-1], popup='Ponto Final', icon=folium.Icon(color='red')).add_to(mapa)
    mapa.save(nomeArq)
    return nomeArq



