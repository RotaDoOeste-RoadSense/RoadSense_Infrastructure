FROM ubuntu:24.04



# (opcional, mas ajuda a build falhar “direito” quando algo dá ruim)
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]

# Ferramentas necessárias para baixar chave e adicionar repositório
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates wget gnupg \
  && rm -rf /var/lib/apt/lists/*


# # download the key to system keyring
# RUN wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB \
# | gpg --dearmor | tee /usr/share/keyrings/oneapi-archive-keyring.gpg > /dev/null

# # add signed entry to apt sources and configure the APT client to use Intel repository:
# RUN echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" | tee /etc/apt/sources.list.d/oneAPI.list

# Adiciona a chave + repo da Intel (sem sudo)
RUN wget -qO- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB \
    | gpg --dearmor -o /usr/share/keyrings/oneapi-archive-keyring.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" \
    > /etc/apt/sources.list.d/oneAPI.list


RUN apt-get update && \
    apt-get install -y \
    libxerces-c3.2 \
    libraw1394-11 \
    libc6 \ 
    libusb-1.0-0 \
    xsdcxx \
    wget \
    libavcodec60 \
    libavformat60 \
    libavutil58 \
    libswscale7 \
    libglu1-mesa \
    libomp5 \
    libglut3.12 \
    libglut-dev \
    libglu1-mesa-dev \
    intel-oneapi-openmp-2025.0 \
    nano \
    gcc \
    g++ \
    xvfb \
    libxerces-c-dev \
    libusb-1.0-0-dev \
    cmake \
    make \
    python3 \
    python-is-python3 \
    python3-pip \
    python3-dev \
    python3-tk \ 
    build-essential \
    pkg-config \
    mariadb-client \
    libmariadb-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-dev \
    libosmesa6-dev \
    mesa-common-dev \
    htop \
    time \
    git \
    && rm -rf /var/lib/apt/lists/*




RUN echo "ladybug ladybug/accepted-flir-eula boolean true" | debconf-set-selections

# Defina o diretório de trabalho para o contêiner
WORKDIR /app
COPY ladybug.deb /app/
RUN dpkg -i ladybug.deb && apt-get install -f -y && rm -rf /var/lib/apt/lists/*


WORKDIR /app


# Copie o arquivo de requisitos, se você tiver
COPY requirements.txt /app/

# Instale as dependências Python, se houver
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages


# Defina o comando padrão para o contêiner
#CMD ["python", "main.py"]

# Build ladybugCubeMap
RUN make -C /usr/src/ladybug/src/ladybugCubeMap

# Sempre rodar como 1000:1000
ARG USER_ID=1000
ARG GROUP_ID=1000

RUN set -eux; \
  # cria grupo 1000 se não existir (nome tanto faz)
  if ! getent group "${GROUP_ID}" >/dev/null; then \
    addgroup --gid "${GROUP_ID}" appgroup; \
  fi; \
  \
  # cria usuário 1000 se não existir (nome tanto faz)
  if ! getent passwd "${USER_ID}" >/dev/null; then \
    GROUP_NAME="$(getent group "${GROUP_ID}" | cut -d: -f1)"; \
    adduser --disabled-password --gecos '' --uid "${USER_ID}" --ingroup "${GROUP_NAME}" appuser; \
  fi; \
  \
  # define HOME baseado no passwd do UID
  HOME_DIR="$(getent passwd "${USER_ID}" | cut -d: -f6)"; \
  mkdir -p "${HOME_DIR}"; \
  chown -R "${USER_ID}:${GROUP_ID}" "${HOME_DIR}"

# importante: HOME precisa existir e ser gravável

ENV DEBIAN_FRONTEND=noninteractive
ENV RABBITMQ_USER=rdt
ENV RABBITMQ_PASSWORD=123456


#RUN apt update && apt install -y parallel

#ENV HOME=/home/appuser
USER 1000:1000
CMD ["bash", "-l"]

