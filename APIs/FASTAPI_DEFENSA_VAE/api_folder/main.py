import os
os.environ['CUDA_LAUNCH_BLOCKING'] = "1"
os.environ['TORCH_USE_CUDA_DSA'] = "1"
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from PIL import Image
import io
from inference import predict, predict_old, predict_crop, predict_crop_similarities
import numpy as np

app = FastAPI()

@app.post("/analyze/")
async def analyze(
    file: UploadFile = File(...),
    x_min: int = Form(...),
    y_min: int = Form(...),
    x_max: int = Form(...),
    y_max: int = Form(...)
):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image = np.array(image)
        box = [x_min, y_min, x_max, y_max]
        response = predict(image, box)
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})
    
@app.post("/analyze_v2/")
async def analyze(
    file: UploadFile = File(...),
    x_min: int = Form(...),
    y_min: int = Form(...),
    x_max: int = Form(...),
    y_max: int = Form(...)
):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image = np.array(image)
        box = [x_min, y_min, x_max, y_max]
        response = predict_old(image, box)
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})
    

@app.post("/analyze_v3/")
async def analyze(
    file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image = np.array(image)
        response = predict_crop(image)
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})
    

@app.post("/analyze_v4/")
async def analyze(
    file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image = np.array(image)
        response = predict_crop_similarities(image)
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8702)
# curl -X POST "http://127.0.0.1:8701/analyze/" -F "file=@path_to_your_image.jpg"