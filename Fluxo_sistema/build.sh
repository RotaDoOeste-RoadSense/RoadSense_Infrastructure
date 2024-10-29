#docker build -t fluxo .

docker rm -f fluxo2

docker run -it --name fluxo2 -v /mnt/windows_share:/mnt/windows_share -v $(pwd):/app --network=host --restart unless-stopped fluxo2
