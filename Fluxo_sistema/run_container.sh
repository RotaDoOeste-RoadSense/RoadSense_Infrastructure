#!/bin/bash

# Nome do container como argumento, padrão para 'fluxo' se não for passado
CONTAINER_NAME=${1:-fluxo}

# Build da imagem
docker build --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg USER_NAME=$(id -un) -t $CONTAINER_NAME .

# Remove container existente, se houver
docker rm -f $CONTAINER_NAME 2>/dev/null

# Executa o container com o nome fornecido
docker run -it --name $CONTAINER_NAME -v /mnt:/mnt/ -v $(pwd):/app -v /home:/home --network=host --restart unless-stopped $CONTAINER_NAME
