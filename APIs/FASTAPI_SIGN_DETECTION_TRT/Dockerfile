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
    "uvicorn[standard]" 
COPY api_folder/ /workspace/api_folder/
WORKDIR /workspace/api_folder/
CMD ["python", "test_engine.py"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8120", "--workers", "9"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8120", "--workers", "1"]