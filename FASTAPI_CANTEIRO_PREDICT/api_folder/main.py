import os

from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from fastapi_versioning import VersionedFastAPI, version

app = FastAPI()

@app.post("/median-exists/")
@version(1)
async def predict(
        lat: float = Form(None),
        lon: float = Form(None)
    ):
    try:
        from v1.inference import get_median 
        result= get_median(lat, lon)
        response={'median_v1':f'{result}'}
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

app = VersionedFastAPI(app,
    version_format='{major}',
    prefix_format='/v{major}',
    enable_latest=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8017)
