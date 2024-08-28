FROM nvidia/cuda:12.5.0-base-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    pkg-config \
    libpq-dev

RUN pip3 install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    sqlalchemy \
    psycopg2-binary \
    python-multipart \
    fastapi-versioning

WORKDIR /app

COPY FASTAPI_GET_NEW_TRECHO/api_folder /app


EXPOSE 8013

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8013"]

# docker build -t minha-imagem-fastapi-cv2:latest .
