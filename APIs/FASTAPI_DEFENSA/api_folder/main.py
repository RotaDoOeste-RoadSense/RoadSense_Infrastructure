import os
os.environ['CUDA_LAUNCH_BLOCKING'] = "1"
os.environ['TORCH_USE_CUDA_DSA'] = "1"

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

@app.post("/analyze")
@version(3)
async def analyze(
    file: UploadFile = File(...),
):
    try:
        from v3.inference import get_defensas
        
        # Read the contents of the uploaded file
        contents = await file.read()
        
        # Open the image using PIL
        image = Image.open(io.BytesIO(contents))
        
        # Use the temporary file path with get_defensas
        response = get_defensas(image)

        return JSONResponse(content=response)

    except Exception as e:
        return {"error": str(e)}

@app.post("/analyze")
@version(2)
async def analyze(
    file: UploadFile = File(...), 
):
  try:
        from v2.inference_trt import get_defensas
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image = np.array(image)
        response = get_defensas(image)  

        return JSONResponse(content=response)
  
  except Exception as e:
        return {"error": str(e)}

@app.post("/analyze")
@version(1)
async def analyze(
    file: UploadFile = File(...), 
):
  try:
        from v1.inference_trt import get_defensas
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image = np.array(image)
        response = get_defensas(image)  

        return JSONResponse(content=response)
  
  except Exception as e:
        return {"error": str(e)}

app = VersionedFastAPI(app,
    version_format='{major}',
    prefix_format='/v{major}',
    enable_latest=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8420)
