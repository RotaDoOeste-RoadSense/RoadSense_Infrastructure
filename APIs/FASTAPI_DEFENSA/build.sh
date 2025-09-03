#docker build -t trt --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .
docker build --rm -t defensa .
docker rm -f defensa
#docker run -it --gpus=0 -v .:/workspace --ipc=host --ulimit memlock=-1 --ulimit stack=6710886 --name trt2 --restart unless-stopped -p 8220:8220 trt

docker run -it --privileged -v .:/app --gpus=all --ipc=host --ulimit memlock=-1 --ulimit stack=6710886 --name defensa --restart unless-stopped -p 8700:8700 defensa bash