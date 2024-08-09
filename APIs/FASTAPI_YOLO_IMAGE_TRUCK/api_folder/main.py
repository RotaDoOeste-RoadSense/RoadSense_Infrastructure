import os
os.environ['CUDA_LAUNCH_BLOCKING'] = "1"
os.environ['TORCH_USE_CUDA_DSA'] = "1"

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from PIL import Image
import io
from inference_trt import get_plates
import numpy as np

app = FastAPI()

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...), 
    classes: str = Form(None)
):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image = np.array(image)
        if classes:
            classes = tuple(map(int,classes.split(',')))
        response = get_plates(image, classes)
        return JSONResponse(content=response)
    except Exception as e:
        print(e)
        return JSONResponse(content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8220)
# curl -X POST "http://127.0.0.1:8000/upload-image/" -F "file=@path_to_your_image.jpg"
