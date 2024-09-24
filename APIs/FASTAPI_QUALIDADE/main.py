from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi_versioning import VersionedFastAPI, version
from typing import List

app = FastAPI()

# Versão 1: Aceita múltiplos arquivos de imagem individuais
@app.post("/qualidade/")
@version(1)
async def qualidade_v1(files: List[UploadFile] = File(...)):
    try:
        from api_folder.v1.inference import process_images
        result = await process_images(files)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

# Versão 2: Aceita um arquivo zip contendo imagens
@app.post("/qualidade/")
@version(2)
async def qualidade_v2(zip_file: UploadFile = File(...)):
    try:
        from api_folder.v2.inference import process_zip_file
        result = await process_zip_file(zip_file)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)})

app = VersionedFastAPI(
    app,
    version_format='{major}',
    prefix_format='/v{major}',
    enable_latest=True
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8330)
