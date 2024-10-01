docker build -t fluxo2 .

docker rm -f fluxo2

docker run -it --name fluxo2 -v /mnt/windows_share/GPS:/mnt/teste -v $(pwd):/app --network=host fluxo2
