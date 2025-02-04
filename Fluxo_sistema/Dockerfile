# Use a imagem oficial do Python 3.10 como base
FROM python:3.10-slim

# Defina o ambiente para não solicitar interatividade durante a instalação
ENV DEBIAN_FRONTEND=noninteractive
ENV RABBITMQ_USER=rdt
ENV RABBITMQ_PASSWORD=123456
# Atualize o sistema e instale o cliente MariaDB, pkg-config e as bibliotecas de desenvolvimento
RUN apt-get update && \
    apt-get install -y \
    gcc \
    g++ \
    make \
    pkg-config \
    mariadb-client \
    libmariadb-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# bibliotecas necessarias para o opencv
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# Defina o diretório de trabalho para o contêiner
WORKDIR /app

# Copie o arquivo de requisitos, se você tiver
 COPY requirements.txt .

# Instale as dependências Python, se houver
RUN pip install --no-cache-dir -r requirements.txt

# Defina o comando padrão para o contêiner
#CMD ["python", "main.py"]
CMD ["bash"]