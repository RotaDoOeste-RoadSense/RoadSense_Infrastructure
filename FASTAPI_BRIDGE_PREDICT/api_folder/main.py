import os

from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from fastapi_versioning import VersionedFastAPI, version

app = FastAPI()

@app.get("/bridge-exists/")
@version(1)
async def predict(
        lat: float = Form(None),
        lon: float = Form(None)
    ):
    try:
        from v1.inference import verify_bridge 
        result= verify_bridge(lat, lon)
        response={'is bridge':f'{result}'}
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

app = VersionedFastAPI(app,
    version_format='{major}',
    prefix_format='/v{major}',
    enable_latest=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8018)
