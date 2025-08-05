from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi_versioning import VersionedFastAPI, version
from PIL import Image
import io
import numpy as np
import logging

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

app = FastAPI()

@app.post("/outflow-detect") 
@version(1)
async def analyze(
    file: UploadFile = File(...),
):
    try:
        from v1.inference_detection import drainage_detect_seg

        contents = await file.read()

        image = Image.open(io.BytesIO(contents))

        response = drainage_detect_seg(image)

        return JSONResponse(content=response)

    except Exception as e:
        return {"error": str(e)}
    
@app.post("/outflow-classify") 
@version(1)
async def analyze(
    file: UploadFile = File(...),
):
    try:
        from v1.inference_classify import drainage_classify

        contents = await file.read()

        image = Image.open(io.BytesIO(contents))

        response = drainage_classify(image)

        return JSONResponse(content=response)

    except Exception as e:
        return {"error": str(e)}