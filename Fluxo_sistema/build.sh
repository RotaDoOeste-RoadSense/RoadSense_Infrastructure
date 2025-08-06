docker build --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg USER_NAME=servidor -t fluxo .

docker rm -f fluxo

docker run -it --name fluxo -v /mnt:/mnt/ -v $(pwd):/app -v /home:/home --network=host --restart unless-stopped fluxo
