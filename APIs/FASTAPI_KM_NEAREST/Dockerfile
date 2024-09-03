FROM nvidia/cuda:12.5.1-base-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    pkg-config \
    libmysqlclient-dev \
    build-essential \
    libpq-dev

RUN pip3 install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    geopy \
    python-multipart \
    fastapi-versioning \
    sqlalchemy \
    psycopg2-binary 
    
WORKDIR /app

COPY api_folder /app

EXPOSE 8023

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8023"]
# CMD ["bash"]
# docker build -t minha-imagem-fastapi-cv2:latest .
