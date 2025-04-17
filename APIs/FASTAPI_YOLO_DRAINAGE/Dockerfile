FROM nvidia/cuda:12.5.0-base-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 

RUN pip3 install --no-cache-dir \
    fastapi \
    torch \
    torchvision \
    fastapi-versioning \
    "uvicorn[standard]" \
    ultralytics \
    pillow \
    python-multipart

RUN ln -s /usr/bin/python3 /usr/bin/python 


WORKDIR /app

COPY api_folder /app

EXPOSE 8035

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8035"]

# docker build -t minha-imagem-fastapi-cv2:latest .
