from fastapi import FastAPI, HTTPException , Form
from fastapi.responses import HTMLResponse
from fastapi_versioning import VersionedFastAPI, version
from sqlalchemy import asc, func
from v3.base import get_session
from v3.models import ImageData, trips, Manutencao, Area, Vegetacao, Trecho
from v3.utils import geraMapa, convert_pano_cube
import pandas as pd
import os
import folium
#import webbrowser

app = FastAPI()

@app.get("/plot-coords-mato/", response_class=HTMLResponse)
@version(3)
async def plotCoords():
    
    try:
        session = get_session()
            
        lastTripId = allDataTrips.trip_id
        folder = allDataTrips.root_folder
        
        lastTripId = 2
        allData = session.query(ImageData.id,ImageData.latitude,ImageData.longitude,Manutencao.situacao,Trecho.ID_TRECHO,Trecho.codigo_rodovia,
                Trecho.quilometragem_trecho,
                ImageData.nome_imagem,
                Area.caracteristicas_area
            ).join(
                Vegetacao, Vegetacao.ID_IMAGE_DATA == ImageData.id
            ).join(
                Area, Area.ID_AREA == Vegetacao.ID_AREA
            ).join(
                Manutencao, Manutencao.ID_AREA == Area.ID_AREA
            ).join(
                Trecho, Trecho.ID_TRECHO == Area.ID_TRECHO
            ).filter(
                ImageData.trip_id == lastTripId
            ).order_by(asc(ImageData.order)).all()
        

       
        lats=[]
        longs=[]
        situacoes = []
        lados=[]
        prev_id = None
        popups = []
        ids=[]

        lats2, longs2, situacoes2, lados2, popups2 = [], [], [], [], []

        session.close()
        for data in allData:
           
            idImg, lat, lon, situacao, trechoid, codigoRod, quilometragem, nomeImg, area = data
            
            #if 1:
            if not ('lateral_Norte' or 'canteiro_Sul') in area:
                if prev_id != idImg:
                    situacoes.append(situacao)
                    lats.append(lat)
                    longs.append(lon)
                    #print(area)
                    lados.append('esquerda')
                    #else:
                    #   lados.append('esquerda')
                    
                    imgCube = convert_pano_cube(str(nomeImg), "Cam1")
                    camImg = folder+'/Cube/' +imgCube
                    conteudoPopup = f"""
                    <div>
                        <h4>ID Trecho: {trechoid}</h4>
                        <p>Rodovia: {codigoRod}</p>
                        <p>Tamanho Trecho: {quilometragem} m</p>
                    
                    </div>
                    """
                    # <img src="{camImg}" alt="Imagem do Trecho" style="width:150px;">
                    popups.append(conteudoPopup)

                prev_id = idImg
            
            




        latitude_media = sum(lats) / len(lats)
        longitude_media = sum(longs) / len(longs)
        mapa = folium.Map(location=[latitude_media, longitude_media], zoom_start=12)

        mapa = geraMapa(mapa, lats, longs, situacoes, lados, popups)

        for data in allData:
           
            idImg, lat, lon, situacao, trechoid, codigoRod, quilometragem, nomeImg, area = data
            if  ('lateral_Norte' or 'canteiro_Sul') in area:

                if prev_id != idImg:
                    situacoes2.append(situacao)
                    lats2.append(lat)
                    longs2.append(lon)
                    #print(area)
                    lados2.append('direita')
                    #else:
                    #   lados.append('esquerda')
                    
                    imgCube = convert_pano_cube(str(nomeImg), "Cam1")
                    camImg = folder+'/Cube/' +imgCube
                    conteudoPopup = f"""
                    <div>
                        <h4>ID Trecho: {trechoid}</h4>
                        <p>Rodovia: {codigoRod}</p>
                        <p>Tamanho Trecho: {quilometragem} m</p>
                    
                    </div>
                    """
                    # <img src="{camImg}" alt="Imagem do Trecho" style="width:150px;">
                    popups2.append(conteudoPopup)

                prev_id = idImg
            


        mapa = geraMapa(mapa, lats2, longs2, situacoes2, lados2, popups2)



        
        mapa.save('v3/mapa.html')



        with open('v3/mapa.html', 'r') as file:
            return HTMLResponse(content=file.read(), status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app = VersionedFastAPI(app,
    version_format='{major}',
    prefix_format='/v{major}',
    enable_latest=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8023)
