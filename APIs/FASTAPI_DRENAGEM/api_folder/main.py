import os
os.environ['CUDA_LAUNCH_BLOCKING'] = "1"
os.environ['TORCH_USE_CUDA_DSA'] = "1"

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi_versioning import VersionedFastAPI, version
from PIL import Image
import io
import numpy as np

app = FastAPI()

''''
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
'''
@app.post("/analyze")
@version(2)
async def analyze(
    file: UploadFile = File(...), 
):
  try:
        from v2.inference_trt import get_drenagens
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image = np.array(image)
        response = get_drenagens(image)  

        return JSONResponse(content=response)
  
  except Exception as e:
        return {"error": str(e)}

app = VersionedFastAPI(app,
    version_format='{major}',
    prefix_format='/v{major}',
    enable_latest=True)
'''
@app.post("/analyze")
@version(1)
async def analyze(
    file: UploadFile = File(...), 
):
  try:
        from v1.inference_trt import get_drenagens
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image = np.array(image)
        response = get_drenagens(image)  

        return JSONResponse(content=response)
  
  except Exception as e:
        return {"error": str(e)}

app = VersionedFastAPI(app,
    version_format='{major}',
    prefix_format='/v{major}',
    enable_latest=True)


'''
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8421)