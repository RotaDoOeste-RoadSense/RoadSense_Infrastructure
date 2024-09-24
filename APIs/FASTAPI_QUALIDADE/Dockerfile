FROM pytorch/pytorch:1.12.1-cuda11.3-cudnn8-runtime

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 

RUN pip install --no-cache-dir \
    fastapi \
    fastapi_versioning \
    "uvicorn[standard]" \
    python-multipart \
    numpy \
    scikit-learn \
    Pillow \
    matplotlib \
    tqdm \
    torchvision

WORKDIR /app

COPY . /app

EXPOSE 8330

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8330"]
