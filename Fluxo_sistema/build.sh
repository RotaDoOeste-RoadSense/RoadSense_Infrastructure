docker build -t fluxo2 . 

docker rm -f fluxo2

docker run -it --name fluxo2 -v /mnt/Viagem3:/mnt/Viagem3 -v .:/app --network=host fluxo2
