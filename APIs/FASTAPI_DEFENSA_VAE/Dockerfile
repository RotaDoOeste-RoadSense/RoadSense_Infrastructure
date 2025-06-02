#FROM python:3.8.12
FROM nvcr.io/nvidia/tensorflow:22.10.1-tf2-py3

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

workdir /app

# RUN pip install alibi-detect[tensorflow]

# RUN pip install opencv-python==4.11.0.86

# RUN pip install tensorflow-probability==0.18.0

# RUN pip install gunicorn fastapi "uvicorn[standard]"

RUN pip3 install --no-cache-dir \
alibi-detect[tensorflow] \
opencv-python==4.11.0.86 \
tensorflow-probability==0.18.0 \
gunicorn \
fastapi \
scikit-learn \
python-multipart \ 
"uvicorn[standard]"



WORKDIR /app/api_folder



COPY api_folder /app/api_folder

RUN cat /app/api_folder/weights/vae.zip.0* > /app/api_folder/weights/vae.zip

RUN unzip /app/api_folder/weights/vae.zip -d /app/api_folder/weights/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8702"]

#COPY requirements_vae.txt /app/requirements.txt

#RUN pip install -r requirements.txt
