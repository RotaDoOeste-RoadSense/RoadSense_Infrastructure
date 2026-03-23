from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi_versioning import VersionedFastAPI, version
from PIL import Image
import io
import numpy as np
import logging
import cv2

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

app = FastAPI()

@app.post("/horizontal-segment") 
@version(1)
async def analyze(
    file: UploadFile = File(...),
):
    try:
        from v1.inference_segment import set_segment

        contents = await file.read()

        image = Image.open(io.BytesIO(contents))
        
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        response = set_segment(image)

        return JSONResponse(content=response)

    except Exception as e:
        return {"error": str(e)}
    
@app.post("/horizontal-classify") 
@version(1)
async def analyze(
    file: UploadFile = File(...),
):
    try:
        from v1.inference_classify import horizontal_classify

        contents = await file.read()

        image = Image.open(io.BytesIO(contents))
        
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        response = horizontal_classify(image)

        return JSONResponse(content=response)

    except Exception as e:
        return {"error": str(e)}