FROM nvcr.io/nvidia/pytorch:22.11-py3
ARG TZ=America/Cuiaba
ENV TZ $TZ
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
WORKDIR /workspace
COPY requirements.txt .
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get install vim nano -y
RUN pip install -r requirements.txt
#COPY . /workspace/
WORKDIR /workspace/
#RUN cat weights/model.* > weights/model.plan
#CMD ["python", "test_engine.py"]

