docker build -t fluxo2 . 

docker rm -f fluxo2

#docker run -it --name fluxo2 -v /mnt/HD12TB/DATASET_TESTE_RONDONOPOLIS:/mnt/HD12TB/DATASET_TESTE_RONDONOPOLIS --network=host fluxo2
docker run -it --name fluxo2 -v /Fuxo_sistema --network=host fluxo2