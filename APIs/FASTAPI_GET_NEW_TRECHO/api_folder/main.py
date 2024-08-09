import os

from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from fastapi_versioning import VersionedFastAPI, version
# from inference import get_trecho
from create_new_trip_id import create_new_trip
# from versao1.teste import resultado as v1_resultado
# from versao2.teste import resultado as v2_resultado
app = FastAPI()

@app.get("/new-trip/")
@version(1,0)
async def new_trip(path: str = Form(None)):
    return JSONResponse(content={'trip_id':create_new_trip(path)})
    # curl -X GET -L http://localhost:8013/new-trip


# @app.get("/retorna-int")
# @version(1,0)
# async def meuint():
#     resultado = v1_resultado()
#     return JSONResponse(content={"valor":resultado})

# @app.get("/retorna-int")
# @version(2,0)
# async def meuint():
#     resultado = v2_resultado()
#     return JSONResponse(content={"valor":resultado})


app = VersionedFastAPI(app,enable_latest=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)
