
FROM nvidia/cuda:12.6.0-cudnn-runtime-ubuntu24.04


RUN apt-get update && apt-get install -y \
    python3-pip 


RUN pip3 install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    opencv-python-headless==4.6.0.66 \
    torch==2.4.1\
    torchvision==0.19.1 \
    python-multipart \
    pillow \ 
    "numpy<2" \
    tqdm \
    Cython \
    onnxruntime-gpu \
    --break-system-packages


WORKDIR /app

COPY api_folder /app/api_folder


WORKDIR /app/api_folder

EXPOSE 8010

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]