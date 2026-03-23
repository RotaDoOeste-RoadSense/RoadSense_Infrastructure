from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
import io

app = FastAPI()
model = YOLO("best.pt")

@app.post("/plate-inference/")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()        
    try:
        image = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception:
        raise HTTPException(status_code=400, detail='erro ao processar imagem')
    
    results = model.predict(image)[0]    
    if results.probs.data[results.probs.top1]<0.80:
        raise HTTPException(
            status_code=422,#requisição ok, porem não pode ser processada
            detail='Baixa probabilidade, resultado não confiavel'
        )
    return JSONResponse(content={
        'results':str(results.probs.top1),
        'conf':float(results.probs.top1conf)
    })
    
