docker build -t fluxo .

docker rm -f fluxo

docker run -it --name fluxo2 -v /mnt/windows_share/GPS:/mnt/teste -v $(pwd):/app --network=host fluxo2
