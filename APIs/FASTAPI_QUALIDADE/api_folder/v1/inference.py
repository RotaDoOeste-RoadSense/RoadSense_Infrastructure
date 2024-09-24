from fastapi import UploadFile
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms

from PIL import Image
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List
from io import BytesIO

# Configurar o dispositivo (CPU ou GPU)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Definir as transformações de imagem (pré-processamento)
transformacao = transforms.Compose([
    transforms.Resize((224, 224)),  # Redimensionar imagens para o tamanho esperado pelo modelo
    transforms.ToTensor(),  # Converter PIL Image para Tensor
    transforms.Normalize(  # Normalizar com médias e desvios padrão do ImageNet
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# Carregar um modelo pré-treinado (por exemplo, ResNet50)
modelo = models.resnet50(pretrained=True)
modelo = modelo.to(device)
modelo.eval()  # Definir o modelo para modo de avaliação

# Remover a última camada de classificação para obter recursos da penúltima camada
modelo = nn.Sequential(*list(modelo.children())[:-1])

async def process_images(files: List[UploadFile]):
    # Lista para armazenar nomes de arquivos e seus recursos correspondentes
    nomes_imagens = []
    recursos = []

    # Processar cada imagem
    with torch.no_grad():
        for uploaded_file in files:
            if uploaded_file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                # Ler a imagem
                image_bytes = await uploaded_file.read()
                imagem = Image.open(BytesIO(image_bytes)).convert('RGB')
                # Pré-processar a imagem
                img = transformacao(imagem).unsqueeze(0).to(device)
                # Extrair recursos
                recurso = modelo(img)
                # Achatar o tensor de recursos e converter para array numpy
                recurso_np = recurso.cpu().numpy().flatten()
                recursos.append(recurso_np)
                nomes_imagens.append(uploaded_file.filename)

    if len(recursos) == 0:
        return {"error": "Nenhuma imagem válida foi fornecida."}

    # Converter a lista de recursos para um array NumPy
    recursos = np.array(recursos)

    # Calcular similaridades cosseno par a par
    matriz_similaridade = cosine_similarity(recursos)

    # Calcular a similaridade média percentual para cada imagem
    similaridades_medias = matriz_similaridade.mean(axis=1) * 100  # Multiplicar por 100 para porcentagem

    # Identificar a imagem mais diferente (com a menor similaridade média)
    indice_mais_diferente = np.argmin(similaridades_medias)
    imagem_mais_diferente = nomes_imagens[indice_mais_diferente]
    pontuacao_mais_diferente = similaridades_medias[indice_mais_diferente]

    # Preparar os resultados
    resultados = {
        "similaridades": {
            nome: f"{similaridade:.2f}%"
            for nome, similaridade in zip(nomes_imagens, similaridades_medias)
        },
        "imagem_mais_diferente": imagem_mais_diferente,
        "similaridade_media": f"{pontuacao_mais_diferente:.2f}%"
    }

    return resultados
