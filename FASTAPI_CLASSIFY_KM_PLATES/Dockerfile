FROM nvidia/cuda:12.5.1-base-ubuntu20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
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
    opencv-python-headless \
    fastapi-versioning \
    timm

WORKDIR /app

COPY api_folder /app

EXPOSE 8015

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8015"]
# CMD ["bash"]
# docker build -t minha-imagem-fastapi-cv2:latest .
