FROM nvcr.io/nvidia/pytorch:22.11-py3

RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 

RUN pip3 install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    opencv-python==4.6.0.66 \
    #torch==2.4.1\
    #torchvision==0.19.1\
    ultralytics==8.0.238 \
    python-multipart \
    pycuda==2024.1 
  
WORKDIR /app

COPY api_folder /app/api_folder

WORKDIR /app/api_folder/weights

RUN cat /app/api_folder/weights/best_a* > /app/api_folder/weights/best.onnx

WORKDIR /app/api_folder


#CMD ["python", "test_engine.py"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8400"]
