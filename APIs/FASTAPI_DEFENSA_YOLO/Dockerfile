FROM nvidia/cuda:12.5.0-base-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 

RUN pip3 install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    ultralytics==8.3.65 \
    opencv-python-headless \
    python-multipart \
    gunicorn

WORKDIR /app/api_folder
COPY api_folder /app/api_folder
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8700"]
