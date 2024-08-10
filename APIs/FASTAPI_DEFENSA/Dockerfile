FROM nvcr.io/nvidia/pytorch:22.11-py3
ARG TZ=America/Cuiaba
ENV TZ $TZ
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
WORKDIR /workspace
COPY api_folder/requirements.txt .
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get install vim nano -y
RUN pip install -r requirements.txt
RUN pip3 install --no-cache-dir \
    fastapi \
    fastapi_versioning 


# para juntar os arquivos usar os dois runs cat models...mode.pat e model.onnx
#RUN cat weights/model.* > weights/model.plan 
#RUN cat weights/yolov8x.* > weights/yolov8x.onnx 

# apenas para test_engine.py (executar o engine antes do docker compose para criar o plan)
#COPY api_folder/ .
#CMD ["python", "v2/test_engine.py"]
# depois executar: docker cp trt2:/workspace/api_folder/v2/weights/model.plan mnt/internal/RoadSense_Infrastructure/APIs/FASTAPI_DEFENSA/api_folder/v2/weights/

# executar após a criação do plan (docker compose up --build)
COPY api_folder/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8420"]

