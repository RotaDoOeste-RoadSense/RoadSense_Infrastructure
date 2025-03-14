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

COPY . /app

RUN cat weights/best.onnx.00* > weights/best.onnx


RUN cat weights/best_fp16.plan.00* > weights/best_fp16.plan


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8600"]

