docker build --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg USER_NAME=$(id -un) -t fluxo2 .

docker rm -f fluxo2

docker run -it --name fluxo2 -v /mnt:/mnt/ -v $(pwd):/app -v /home:/home --network=host fluxo2
