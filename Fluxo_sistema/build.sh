docker build -t fluxo .

docker rm -f fluxo

docker run -it --name fluxo -v /mnt:/mnt/ -v $(pwd):/app --network=host --restart unless-stopped fluxo
