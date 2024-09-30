#docker build -t vegetation .

docker rm -f vegetation

docker run -it -v .:/workspace -v /mnt/windows_share:/workspace/windows_share --gpus='"device=1"' --name vegetation --ipc=host --ulimit memlock=-1 --ulimit stack=67108864 vegetation bash