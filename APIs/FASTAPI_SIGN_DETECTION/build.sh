docker build -t mato .
docker rm -f mato

docker run -it -v .:/app --gpus='"device=0"' --privileged --rm -p 8010:8010 --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 --name mato mato bash