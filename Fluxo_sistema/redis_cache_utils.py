"""
Módulo utilitário para cache Redis compartilhado entre scripts do RoadSense_Infrastructure.
Centraliza cliente, funções de cache para imagens e APIs, com TTL 24h e LRU 500GB.
"""

import os
import redis
import hashlib
import json
import io
import cv2
import numpy as np
from typing import Optional, Dict, Any

# Carrega configurações via variáveis de ambiente para segurança (mitiga hardcoded passwords)
REDIS_HOST = os.getenv('REDIS_HOST', '192.168.18.253')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6380))
REDIS_PASS = os.getenv('REDIS_PASSWORD', 'rdt_cache_pass')

# Cliente Redis singleton
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASS,
    db=0,
    decode_responses=False  # Mantém bytes para imagens
)

# TTL padrão de 24 horas (configurável por função)
DEFAULT_TTL = 86400


def get_image_key(file_path: str) -> str:
    """
    Gera chave única para cache de imagem via hash SHA256 do path.

    Args:
        file_path: Path completo da imagem (ex: /mnt/HD/image.jpg)

    Returns:
        Chave Redis no formato 'img:hash'
    """
    return f"img:{hashlib.sha256(file_path.encode()).hexdigest()}"


def get_api_key(endpoint: str, **params) -> str:
    """
    Gera chave única para cache de resposta de API via hash dos parâmetros.

    Args:
        endpoint: Nome ou URL do endpoint (ex: 'gps_predict', 'yolo')
        **params: Parâmetros da requisição como kwargs (ex: lat=1.0, lon=2.0)

    Returns:
        Chave Redis no formato 'api:{endpoint}:hash'
    """
    # Ordena params para consistência (lat=1,lon=2 == lon=2,lat=1)
    params_str = '|'.join(f"{k}:{v}" for k, v in sorted(params.items()))
    hash_val = hashlib.sha256(params_str.encode()).hexdigest()
    return f"api:{endpoint}:{hash_val}"


def escreve(arq, lock, texto):
    with lock:
        with open(arq, "a") as f:
            f.write(texto + "\n")


# def cache_image(file_path: str, ttl: int = DEFAULT_TTL, quality: int = 95, api_name = '', lock = False) -> Optional[bytes]:
#     """
#     Carrega imagem do Redis cache ou path, retorna bytes JPEG.
#     Armazena no cache se miss.

#     Args:
#         file_path: Path da imagem no disco
#         ttl: Tempo de expiração em segundos (default 24h)
#         quality: Qualidade JPEG (0-100, default 95)

#     Returns:
#         Bytes JPEG da imagem, ou None em erro
#     """
#     key = get_image_key(file_path)

#     # Verifica cache primeiro
#     cached_bytes = redis_client.get(key)
#     if cached_bytes is not None:
#         # if api_name != '' and lock != False:
#         #     escreve(api_name+'_debug.txt', lock, f"Imagem {file_path} carregada do cache")
#         return cached_bytes

#     # Cache miss: carrega do path
#     imagem = cv2.imread(file_path)
#     # if api_name != '' and lock != False:
#     #     escreve(api_name+'_debug.txt', lock, f"Imagem {file_path} carregada do Disco")
#     if imagem is None:
#         raise ValueError(f"Erro ao ler imagem: {file_path}")

#     # Codifica para JPEG bytes
#     success, buffer = cv2.imencode('.jpg', imagem, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
#     if not success:
#         raise ValueError(f"Erro ao codificar imagem: {file_path}")

#     img_bytes = buffer.tobytes()

#     # Armazena no Redis com TTL
#     redis_client.setex(key, ttl, img_bytes)

#     return img_bytes


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
    if cached_bytes is not None:
        # if api_name != '':
        #      escreve(api_name +'_debug.txt', lock, f"Imagem {file_path} carregada do cache")
        return cached_bytes

    # Cache miss: carrega do path
    imagem = cv2.imread(file_path)
    # if api_name != '':
    #      escreve(api_name+'_debug.txt', lock, f"Imagem {file_path} carregada do Disco")
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



def cache_api_response(endpoint: str, params: Dict[str, Any], fetch_fn, ttl: int = DEFAULT_TTL) -> Optional[Dict]:
    """
    Cache genérico para respostas de API JSON.

    Args:
        endpoint: Nome do endpoint (ex: 'gps_predict')
        params: Dicionário com parâmetros da requisição
        fetch_fn: Função callable que executa a requisição (ex: lambda: requests.post(...))
        ttl: Tempo de expiração em segundos (default 24h)

    Returns:
        Dict com resposta JSON, ou None em erro
    """
    key = get_api_key(endpoint, **params)

    # Verifica cache primeiro
    cached_response = redis_client.get(key)
    if cached_response is not None:
        return json.loads(cached_response.decode('utf-8'))

    # Cache miss: executa requisição via função fornecida
    try:
        response_data = fetch_fn()
        if response_data is not None:
            # Armazena no Redis com TTL
            redis_client.setex(key, ttl, json.dumps(response_data))
        return response_data
    except Exception as e:
        print(f"Erro em cache_api_response para {endpoint}: {e}")
        return None


def clear_cache_by_prefix(prefix: str) -> int:
    """
    Remove todas as chaves com prefixo específico (ex: 'img:', 'api:gps_predict:').

    Args:
        prefix: Prefixo das chaves a deletar

    Returns:
        Número de chaves deletadas
    """
    cursor = 0
    deleted = 0
    while True:
        cursor, keys = redis_client.scan(cursor, match=f"{prefix}*", count=1000)
        if keys:
            deleted += redis_client.delete(*keys)
        if cursor == 0:
            break
    return deleted


def get_cache_stats() -> Dict[str, Any]:
    """
    Retorna estatísticas do Redis (uso de memória, total de chaves).

    Returns:
        Dict com 'used_memory', 'maxmemory', 'total_keys'
    """
    info = redis_client.info('memory')
    total_keys = redis_client.dbsize()
    return {
        'used_memory': info.get('used_memory_human', 'N/A'),
        'maxmemory': info.get('maxmemory_human', 'N/A'),
        'total_keys': total_keys
    }
