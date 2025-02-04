#!/bin/bash

# Nome do container como argumento, padrão para 'fluxo' se não for passado
CONTAINER_NAME=${1:-fluxo}

# Build da imagem
docker build -t $CONTAINER_NAME .

# Remove container existente, se houver
docker rm -f $CONTAINER_NAME 2>/dev/null

# Executa o container com o nome fornecido
docker run -it --name $CONTAINER_NAME -v /mnt:/mnt/ -v $(pwd):/app --network=host --restart unless-stopped $CONTAINER_NAME
