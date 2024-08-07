docker build -t fluxo2 . 

docker rm -f fluxo2

docker run -it --name fluxo2 -v /mnt/teste2/Viagem3:/mnt/teste2/Viagem3 --network=host fluxo2
