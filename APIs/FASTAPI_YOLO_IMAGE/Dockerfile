FROM nvidia/cuda:12.5.0-base-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 
    
# RUN apt-get update && apt-get install -y \
#     python3-pip \
#     python3-opencv
# RUN apt-get update && apt-get install -y \
#     python3-pip \
#     python3-opencv \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    ultralytics \
    opencv-python-headless \
    python-multipart

WORKDIR /app

COPY api_folder /app

EXPOSE 8010

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]

# docker build -t minha-imagem-fastapi-cv2:latest .
