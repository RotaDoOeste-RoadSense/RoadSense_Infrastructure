import os

from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from fastapi_versioning import VersionedFastAPI, version

app = FastAPI()

@app.post("/get-highway-number/")
@version(1)
async def predict(
        lat: float = Form(None),
        lon: float = Form(None)
    ):
    try:
        from v1.inference import get_highway_number
        result= get_highway_number(lat, lon)
        response={'highway':f'{result}'}
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

app = VersionedFastAPI(app,
    version_format='{major}',
    prefix_format='/v{major}',
    enable_latest=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8021)
