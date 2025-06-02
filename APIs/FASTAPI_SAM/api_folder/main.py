import os
os.environ['CUDA_LAUNCH_BLOCKING'] = "1"
os.environ['TORCH_USE_CUDA_DSA'] = "1"
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from PIL import Image
import io
from inference import predict
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
        print('salvando imagem')
        image.save('/app/api_folder/temp.png')
        image = np.array(image)
        box = [x_min, y_min, x_max, y_max]
        print(image.shape, box)
        response = predict(image, box)
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8703)
# curl -X POST "http://127.0.0.1:8700/analyze/" -F "file=@path_to_your_image.jpg"