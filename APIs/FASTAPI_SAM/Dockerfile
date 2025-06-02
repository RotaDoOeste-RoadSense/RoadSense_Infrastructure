FROM nvidia/cuda:12.5.0-base-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git

RUN pip3 install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    ultralytics==8.3.65 \
    opencv-python-headless \
    python-multipart \
    gunicorn

RUN pip3 install --no-cache-dir "git+https://github.com/facebookresearch/segment-anything.git" 

WORKDIR /app/api_folder
COPY api_folder /app/api_folder

RUN cat /app/api_folder/weights/sam_vit_l_0b3195.pth.0* > /app/api_folder/weights/sam_vit_l_0b3195.pth


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8703"]
