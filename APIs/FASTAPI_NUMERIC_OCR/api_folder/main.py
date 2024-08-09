import os
os.environ['CUDA_LAUNCH_BLOCKING'] = "1"
os.environ['TORCH_USE_CUDA_DSA'] = "1"
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi_versioning import VersionedFastAPI, version
from PIL import Image
import io
from inference import make_inference
app = FastAPI()
@app.post("/ocr/get_km")
@version(1,0)
async def analyze(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        response = make_inference(image)
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

app = VersionedFastAPI(app,enable_latest=True)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8014)
# curl -X POST "http://localhost:8014/v1_0/ocr/get_km" -F "file=@todos/omni7_20220310_170343_24506078_Panoramic_017050_40940_031-6642_7.jpg"
