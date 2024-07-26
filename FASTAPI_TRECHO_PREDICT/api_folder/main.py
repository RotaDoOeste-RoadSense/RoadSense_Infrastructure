import os

from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from inference import *

app = FastAPI()

@app.get("/get-segment/")
async def predict(
        lat: float = Form(None),
        lon: float = Form(None)
                                ):
    try:
        #print([lat,lon)
        result, min_distance = get_trecho(lat, lon)
        #print(result)
        response={'id':f'{result}', 'min_distance' : min_distance}
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

@app.get("/median-exists/")
async def predict(
        lat: float = Form(None),
        lon: float = Form(None)
                                ):
    try:
        result= get_median(lat, lon)
        response={'median':f'{result}'}
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)
