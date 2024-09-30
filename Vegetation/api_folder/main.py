import os
os.environ['CUDA_LAUNCH_BLOCKING'] = "1"
os.environ['TORCH_USE_CUDA_DSA'] = "1"

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from PIL import Image
import io
from inference_trt import get_class
import numpy as np

app = FastAPI()


async def process(file, version):

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        response = get_class(image,version=version)  

        return response
    except Exception as e:
        print(e)
        return {"error": str(e)}


# Função que processa 4 classes 
@app.post("/analyze_4classes/")
async def analyze_v1(
    file: UploadFile = File(...),
):
    content = await process(file, version=1)
    return JSONResponse(content=content)



# Função que processa 3 classes
@app.post("/analyze/")
async def analyze(
    file: UploadFile = File(...),
):
   content = await process(file, version=0)

   return JSONResponse(content=content)

# Função principal para iniciar o servidor
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8300)
