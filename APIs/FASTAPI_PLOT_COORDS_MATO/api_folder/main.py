from fastapi import FastAPI, HTTPException , Form
from fastapi.responses import HTMLResponse
from fastapi_versioning import VersionedFastAPI, version
from sqlalchemy import asc, func
from v2.base import get_session
from v2.models import ImageData, trips, Manutencao, Area, Vegetacao, Trecho
from v2.utils import geraMapa
import pandas as pd
import os
#import webbrowser

app = FastAPI()

@app.get("/plot-coords-mato/", response_class=HTMLResponse)
@version(2)
async def plotCoords():
    
    try:
        session = get_session()
        
        lastTripId = session.query(func.max(trips.trip_id)).scalar()
        #lastTripId = 
        allData = session.query(ImageData.id, ImageData.latitude,ImageData.longitude,Manutencao.situacao
        ).join(
            Vegetacao, Vegetacao.ID_IMAGE_DATA == ImageData.id
        ).join(
            Area, Area.ID_AREA == Vegetacao.ID_AREA
        ).join(
            Manutencao, Manutencao.ID_AREA == Area.ID_AREA
        ).filter(
            ImageData.trip_id == lastTripId
        ).order_by(asc(ImageData.order)).all()
        
        
        '''
        allDataTrecho = session.query(Trecho.ID_TRECHO,Trecho.codigo_rodovia,Trecho.quilometragem_trecho
        ).join(
            Vegetacao, Vegetacao.ID_IMAGE_DATA == ImageData.id
        ).join(
            Area, Area.ID_AREA == Vegetacao.ID_AREA
        ).join(
            Trecho, Trecho.ID_TRECHO == Area.ID_TRECHO
        ).filter(
            ImageData.trip_id == lastTripId
        ).order_by(asc(ImageData.order)).all()
        '''
       
        lats=[]
        longs=[]
        situacoes = []
        lados=[]
        prev_id = None
        for id, lat, lon, situacao in allData:
            if prev_id != id:
                situacoes.append(situacao)
                lats.append(lat)
                longs.append(lon)
                lados.append('direita')
            prev_id = id
   
        session.close()
     
        mapa = geraMapa(lats, longs, situacoes, lados)
        
        
        with open(mapa, 'r') as file:
            return HTMLResponse(content=file.read(), status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app = VersionedFastAPI(app,
    version_format='{major}',
    prefix_format='/v{major}',
    enable_latest=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8022)
