import redis
import hashlib
import json
import io
import cv2
import numpy as np
from typing import Optional, Dict, Any
from multiprocessing import Lock

from time import time

global_lock = Lock()


# Cliente Redis singleton (ajuste host/port conforme ambiente)
redis_client = redis.Redis(
    host='192.168.18.253',  # Use 'redis' se rodar dentro do docker-compose
    port=6380,  # Porta externa; use 6379 se interno ao compose
    password='rdt_cache_pass',
    db=0,
    decode_responses=False  # Mantém bytes para imagens
)

# TTL padrão de 24 horas (configurável por função)
DEFAULT_TTL = 86400


def escreve(arq, lock, texto):
    with lock:
        with open(arq, "a") as f:
            f.write(texto + "\n")


def cache_image(file_path: str, ttl: int = DEFAULT_TTL, quality: int = 95, api_name = '', lock = False) -> Optional[bytes]:
    """
    Carrega imagem do Redis cache ou path, retorna bytes JPEG.
    Armazena no cache se miss.

    Args:
        file_path: Path da imagem no disco
        ttl: Tempo de expiração em segundos (default 24h)
        quality: Qualidade JPEG (0-100, default 95)

    Returns:
        Bytes JPEG da imagem, ou None em erro
    """
    #key = get_image_key(file_path)
    key = file_path

    # Verifica cache primeiro
    cached_bytes = redis_client.get(key)
    #cached_bytes = None
    if cached_bytes is not None:
        if api_name != '':
             escreve(api_name +'_debug.txt', lock, f"Imagem {file_path} carregada do cache")
        return cached_bytes

    # Cache miss: carrega do path
    imagem = cv2.imread(file_path)
    if api_name != '':
         escreve(api_name+'_debug.txt', lock, f"Imagem {file_path} carregada do Disco")
    if imagem is None:
        raise ValueError(f"Erro ao ler imagem: {file_path}")

    # Codifica para JPEG bytes
    success, buffer = cv2.imencode('.jpg', imagem, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not success:
        raise ValueError(f"Erro ao codificar imagem: {file_path}")

    img_bytes = buffer.tobytes()

    # Armazena no Redis com TTL
    redis_client.setex(key, ttl, img_bytes)

    return img_bytes


#folder = "/mnt/hd1/Extracoes/PGRS_2025"



key = '/mnt/hd1/Extracoes/PGRS_2025/Cube/subindoserra_Cube_004438_cam0.jpg'

start = time()
img = cache_image(key, api_name='test', lock=global_lock)

tempo = time() - start

print(f'demorou {tempo*1000} ms')

start = time()
img = cache_image(key, api_name='test', lock=global_lock)


tempo = time() - start

print(f'demorou {tempo*1000} ms')



# img2 = cv2.imread(key)

# _, buffer = cv2.imencode('.jpg', img2)
# imagem_bytes = io.BytesIO(buffer).getvalue()

# print(len(img), len(imagem_bytes))

# print(img == imagem_bytes)