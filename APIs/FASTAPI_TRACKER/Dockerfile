FROM nvidia/cuda:12.6.0-cudnn-runtime-ubuntu24.04

RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    torch==2.4.1 \
    torchvision==0.19.1 \
    opencv-python-headless==4.6.0.66 \
    "numpy<2" \
    tqdm \
    python-multipart \
    pillow \
    kornia \
    matplotlib \
    requests \
    --break-system-packages

WORKDIR /app

COPY api_folder /app/api_folder
COPY LightGlue /app/LightGlue
COPY weights /app/api_folder/weights

# O pyproject do LightGlue espera requirements.txt.
RUN printf "torch\nnumpy<2\nopencv-python-headless==4.6.0.66\nkornia\n" > /app/LightGlue/requirements.txt \
    && python3 -m pip install --no-cache-dir /app/LightGlue --break-system-packages

WORKDIR /app/api_folder

EXPOSE 8714

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8714", "--workers", "1"]
