#docker build -t trt --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .
#!/bin/bash
set -o allexport
source .env
set +o allexport

# Usar as variáveis
echo "VAR1 is $NAME"
echo "VAR2 is $PORT"

IMAGENAME="trt_${NAME}"
echo $IMAGENAME
docker build -t $IMAGENAME .
# docker rm -f trt2
# #docker run -it --gpus=0 -v .:/workspace --ipc=host --ulimit memlock=-1 --ulimit stack=6710886 --name trt2 --restart unless-stopped -p 8220:8220 trt

# #docker run -it --gpus='device=1' -v .:/workspace --ipc=host --ulimit memlock=-1 --ulimit stack=6710886 --name trt2 --restart unless-stopped -p 8420:8420 trt bash
docker run -it --gpus='device=1' --ipc=host --ulimit memlock=-1 --ulimit stack=6710886 --name $IMAGENAME --restart unless-stopped -p $PORT:8420 $IMAGENAME