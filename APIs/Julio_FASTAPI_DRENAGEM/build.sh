#docker build -t trt --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .
docker build -t trt .
docker rm -f trt2
#docker run -it --gpus=0 -v .:/workspace --ipc=host --ulimit memlock=-1 --ulimit stack=6710886 --name trt2 --restart unless-stopped -p 8220:8220 trt

#docker run -it --gpus='device=1' -v .:/workspace --ipc=host --ulimit memlock=-1 --ulimit stack=6710886 --name trt2 --restart unless-stopped -p 8420:8420 trt bash
docker run -it --gpus='device=0' -v .:/workspace --ipc=host --ulimit memlock=-1 --ulimit stack=6710886 --name trt2 --restart unless-stopped -p 8421:8421 trt bash