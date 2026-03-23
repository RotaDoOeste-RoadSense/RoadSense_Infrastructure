import os
os.environ['CUDA_LAUNCH_BLOCKING'] = "1"
os.environ['TORCH_USE_CUDA_DSA'] = "1"

from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from inference import get_gps

app = FastAPI()

@app.post("/predict/")
async def predict(
        lat: float = Form(None),
        lon: float = Form(None),
        x1: float = Form(None),
        y1: float = Form(None),
        x2: float = Form(None),
        y2: float = Form(None),
        cls: int = Form(None)
                                ):
    try:
        print([lat,lon,x1,y1,x2,y2,cls])
        result = get_gps([lat,lon,x1,y1,x2,y2,cls])
        print(result)
        response={'dlat':f'{result[0]:.15f}','dlon':f'{result[1]:.15f}'}
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)