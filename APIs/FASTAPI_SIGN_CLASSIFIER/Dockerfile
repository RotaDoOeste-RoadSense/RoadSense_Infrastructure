FROM nvidia/cuda:12.6.0-cudnn-runtime-ubuntu24.04


RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    fastapi-versioning \
    opencv-python-headless==4.6.0.66 \
    torch==2.4.1 \
    torchvision==0.19.1 \
    python-multipart \
    pillow \
    "numpy<2" \
    tqdm \
    ultralytics==8.3.75 \
    Cython \
    onnxruntime-gpu \
    --break-system-packages


RUN ln -s /usr/bin/python3 /usr/bin/python 

WORKDIR /app

COPY api_folder /app



EXPOSE 8016

#CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8016", "--workers", "9"]
#CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8016", "--workers", "8"]
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8016", "--workers", "1"]


# docker build -t minha-imagem-fastapi-cv2:latest .
