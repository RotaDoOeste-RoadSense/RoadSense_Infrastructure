#docker build --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg USER_NAME=$(id -un) -t fluxo .

docker build -t fluxo .



docker rm -f fluxo

#docker run -it --name fluxo -v /mnt:/mnt/ -v $(pwd):/app -v /home:/home --network=host --gpus='"device=0"' --privileged fluxo
#docker run -it --name fluxo -v /mnt:/mnt/ -v $(pwd):/app -v "/home/$(id -un)":/home/$(id -un) fluxo



docker run -it --name fluxo \
  --user "$(id -u):$(id -g)" \
  --network=host --privileged \
  -v /mnt:/mnt \
  -v /media:/media \
  -v "$(pwd)":/app \
  -v "/home/$(id -un)":/home/$(id -un) \
  fluxo

# docker run -it --name fluxo \
#   --user 1000:1000 \
#   -e HOME=/home/user \
#   -v /mnt:/mnt \
#   -v "$(pwd):/app" \
#   -v "/home/$(id -un):/home/user" \
#   --network=host --privileged \
#   fluxo