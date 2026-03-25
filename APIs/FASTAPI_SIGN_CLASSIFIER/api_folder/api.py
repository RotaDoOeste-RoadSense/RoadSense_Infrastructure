from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
#from ultralytics import YOLO
from PIL import Image
import io
#from model_cls import Model
import numpy as np
from inference import get_class

app = FastAPI()
#model = YOLO("best.pt")
#model = Model("weights/plate_quality.onnx")

@app.post("/plate-inference/")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()        
    try:
        image = Image.open(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail='erro ao processar imagem')
    image = np.array(image)
    results = get_class(image)
    print(results)
    if "erro_modelo" in results:
        raise HTTPException(status_code=500, detail=str(results["erro_modelo"]))
    if results['Score']<0.80:
        raise HTTPException(
            status_code=422,#requisição ok, porem não pode ser processada
            detail='Baixa probabilidade, resultado não confiavel'
        )
    return JSONResponse(content={
        'results':str(results['Label']),
        'conf':float(results['Score'])
    })
    
