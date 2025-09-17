#FROM nvidia/cuda:12.5.0-base-ubuntu22.04
FROM nvidia/cuda:12.6.0-cudnn-runtime-ubuntu24.04


RUN apt-get update && apt-get install -y \
    python3-pip 

# RUN apt-get update && apt-get install -y \
#     python3-pip \
#     libgl1-mesa-glx \
#     libglib2.0-0 

RUN pip3 install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    opencv-python-headless==4.6.0.66 \
    torch==2.4.1\
    torchvision==0.19.1 \
    "numpy<2" \
    python-multipart \
    pillow \
    #torch==2.8.0 \
    onnxruntime-gpu \ 
    tqdm \
    Cython \
    gunicorn \ 
    --break-system-packages

WORKDIR /app/api_folder
COPY api_folder /app/api_folder
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8700"]
