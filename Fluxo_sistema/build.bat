docker build -t fluxo2 .

docker rm -f fluxo2

docker run -it --name fluxo2 -v E:/Extracoes/:/mnt/windows_share/ -v .:/app --network=host fluxo2
