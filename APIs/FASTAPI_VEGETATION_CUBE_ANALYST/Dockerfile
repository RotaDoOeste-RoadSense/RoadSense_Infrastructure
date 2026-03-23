#FROM nvcr.io/nvidia/pytorch:22.11-py3

#FROM ubuntu:24.04
FROM nvidia/cuda:12.6.0-cudnn-runtime-ubuntu24.04



RUN apt-get update && apt-get install -y \
    python3-pip 


RUN pip3 install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
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

RUN pip3 install --no-cache-dir \
    matplotlib \
    scikit-learn \
    --break-system-packages
  
WORKDIR /workspace

COPY api_folder /workspace/api_folder

WORKDIR /workspace/api_folder

#RUN cat weights/best_a* > weights/best.onnx

#CMD ["python", "test_engine.py"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8500"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8500","--workers", "10"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8500","--workers", "1"]

