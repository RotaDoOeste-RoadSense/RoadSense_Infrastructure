docker build --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) -t mato .
docker rm -f mato

#docker run -it -v .:/app -v /home/rdt/Desktop:/home/rdt/Desktop --gpus='"device=0"' --rm -p 8401:8401 --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 --name mato mato bash
#docker run -it -v .:/app --gpus='"device=0"' --rm -p 8400:8400 --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 --name mato mato
docker run -it -v .:/workspace --gpus='"device=0"' --rm -p 8400:8400 --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 --name mato mato bash