# FROM nvidia/cuda:12.5.0-base-ubuntu22.04

# RUN apt-get update && apt-get install -y \
#     python3-pip \
#     libgl1-mesa-glx \
#     libglib2.0-0 

FROM nvidia/cuda:12.6.0-cudnn-runtime-ubuntu24.04

RUN apt-get update && apt-get install -y \
    python3-pip 


# RUN pip3 install --no-cache-dir \
#     fastapi \
#     fastapi-versioning \
#     "uvicorn[standard]" \

#     #ultralytics \
#     pillow \
#     python-multipart


RUN pip3 install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    fastapi-versioning \
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

RUN ln -s /usr/bin/python3 /usr/bin/python 


WORKDIR /app

COPY api_folder /app

EXPOSE 8024

WORKDIR /app/api_folder

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8024"]

# docker build -t minha-imagem-fastapi-cv2:latest .
