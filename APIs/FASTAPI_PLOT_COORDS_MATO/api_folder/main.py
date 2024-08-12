from fastapi import FastAPI, HTTPException , Form
from fastapi.responses import HTMLResponse
from fastapi_versioning import VersionedFastAPI, version
from v1.base import get_session
from v1.models import ImageData
from v1.utils import geraMapa
import pandas as pd
import os
#import webbrowser

app = FastAPI()

@app.get("/plot-coords-mato/", response_class=HTMLResponse)
@version(1)
async def plotCoords():
    
    try:
    
        #por enquanto ta puxando do csv pois no banco ainda não tem as duas colunas que preciso  
        
        dfAll = pd.read_csv('v1/IMAGE_DATA_202408081209.csv')
        df = dfAll.iloc[4000:5000]
        lats = df['latitude']
        longs = df['longitude']
        porcentMatos = df['percentageMato']
        lados = df['Lados']
        coordenadas =[]
        #session = get_session()
        #coordenadas = session.query(ImageData.latitude, ImageData.longitude).all()
        
        #trecho = coordenadas[:700]

        
        #coordenadas.append(coord_ini)
        #coordenadas.append(coord_fin)
        
        #session.close()
        #if not coordenadas:
        #    raise HTTPException(status_code=404, detail="Nenhuma coordenada encontrada.")
        
        mapa = geraMapa(lats, longs, porcentMatos, lados)
        
        # Abre o arquivo HTML no navegador padrão
        #webbrowser.open(f"file://{os.path.realpath(mapa)}")
        
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
