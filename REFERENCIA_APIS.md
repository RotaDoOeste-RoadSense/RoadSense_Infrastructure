# RoadSense Infrastructure - Referência de APIs

## 🌐 Mapa da Rede e Portas

| Serviço | Porta | Nome Sugerido | Descrição |
| :--- | :--- | :--- | :--- |
| **Trip Manager** | `8013` | `FASTAPI_TRIP_MANAGER` | Gestão de viagens e pastas |
| **Sign Detector** | `8010` | `FASTAPI_SIGN_DETECTOR` | Detecção de placas (Vertical) |
| **Sign Classifier** | `8016` | `FASTAPI_SIGN_CLASSIFIER` | Classificação de qualidade da placa |
| **Tracker** | `8714` | `FASTAPI_TRACKER` | Rastreamento de placas |
| **Guardrail Detector** | `8700` | `FASTAPI_GUARDRAIL_DETECTOR` | Detecção de defensas |
| **Guardrail Quality** | `8702` | `FASTAPI_GUARDRAIL_QUALITY` | Análise de anomalias (VAE) |
| **Guardrail Segmenter** | `8703` | `FASTAPI_GUARDRAIL_SEGMENTER` | Segmentação precisa (SAM) |
| **Drainage Detector** | `8035` | `FASTAPI_DRAINAGE_DETECTOR` | Bueiros e galerias |
| **Outflow Detector** | `8421` | `FASTAPI_OUTFLOW_DETECTOR` | Saídas de água |
| **Horizontal Mapping** | `8024` | `FASTAPI_HORIZONTAL_ANALYST` | Faixas e sinalização horizontal |
| **Vegetation Analyst** | `8500` | `FASTAPI_VEGETATION_CUBE` | Altura do mato em Cubemaps |
| **GPS Predictor** | `8011` | `FASTAPI_GEO_GPS_PREDICTOR` | Predição de coords geográficas |
| **Database (SQL)** | `1111` | `SQL` | PostgreSQL + PostGIS |
| **Redis Cache** | `6381` | `REDIS` | Cache de imagens e respostas |
| **RabbitMQ** | `15673` | `RABBITMQ` | Interface de gestão de filas |

---

## 📋 Índice de APIs

- [1. Gerenciamento de Viagens](#1-gerenciamento-de-viagens)
- [2. Detecção e Classificação de Placas](#2-detecção-e-classificação-de-placas)
- [3. Análise de Defensas](#3-análise-de-defensas)
- [4. Elementos de Drenagem](#4-elementos-de-drenagem)
- [5. Sinalização Horizontal](#5-sinalização-horizontal)
- [6. Vegetação](#6-vegetação)
- [7. Geolocalização e GPS](#7-geolocalização-e-gps)
- [8. Informações Geoespaciais](#8-informações-geoespaciais)

---

## 1. Gerenciamento de Viagens

### 1.1 FASTAPI_TRIP_MANAGER
**Porta**: 8013  
**Descrição**: Gerencia a criação e registro de novas viagens

#### Endpoint
```
POST /new-trip/
```

#### Parâmetros (Form Data)
| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| path | string | Sim | Caminho completo da pasta com dados da viagem |
| way | string | Não | Direção: 'N' (Norte) ou 'S' (Sul) |
| starting_city | string | Não | Cidade de origem |
| ending_city | string | Não | Cidade de destino |
| production | boolean | Não | Se é ambiente de produção (default: false) |

#### Exemplo de Requisição
```bash
curl -X POST "http://localhost:8013/new-trip/" \
  -F "path=/mnt/hd1/Extracoes/PGRS_2025" \
  -F "way=N" \
  -F "starting_city=Rondonópolis" \
  -F "ending_city=Cuiabá" \
  -F "production=false"
```

#### Exemplo de Resposta
```json
{
  "trip_id": 9,
  "message": "Trip created successfully"
}
```

---

## 2. Detecção e Classificação de Placas

### 2.1 FASTAPI_SIGN_DETECTOR
**Porta**: 8010  
**Descrição**: Localiza placas e elementos viários em imagens

#### Endpoint
```
POST /analyze/
```

#### Parâmetros
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| file | File | Imagem para análise (JPEG/PNG) |
| classes | string | Classes a detectar (opcional), ex: "0,1,2" |

#### Exemplo de Requisição
```bash
curl -X POST "http://localhost:8010/analyze/" \
  -F "file=@/caminho/para/imagem.jpg" \
  -F "classes=0,1,2"
```

#### Exemplo de Resposta
```json
{
  "detections": [
    {
      "class": 0,
      "class_name": "placa_regulamentacao",
      "confidence": 0.95,
      "bbox": [100, 150, 300, 400],
      "x1": 100,
      "y1": 150,
      "x2": 300,
      "y2": 400
    },
    {
      "class": 1,
      "class_name": "placa_advertencia",
      "confidence": 0.87,
      "bbox": [450, 200, 600, 380]
    }
  ],
  "total_detections": 2
}
```

### 2.2 FASTAPI_SIGN_CLASSIFIER
**Porta**: 8016  
**Descrição**: Classifica a qualidade da placa detectada

#### Endpoint
```
POST /plate-inference/
```

#### Parâmetros
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| file | File | Imagem da placa para classificar |

#### Exemplo de Requisição
```bash
curl -X POST "http://localhost:8016/plate-inference/" \
  -F "file=@placa_cortada.jpg"
```

#### Exemplo de Resposta
```json
{
  "results": "0",
  "conf": 0.98
}
```

### 2.3 FASTAPI_TRACKER
**Porta**: 8714  
**Descrição**: Rastreamento de detecções entre frames

#### Endpoints
```
GET /health
POST /track/
POST /extract-match/
```

#### Exemplo de Requisição
```bash
curl -X GET "http://localhost:8714/health"
```

#### Exemplo de Resposta
```json
{
  "status": "ok",
  "models_loaded": true
}
```

---

## 3. Análise de Defensas

### 3.1 FASTAPI_GUARDRAIL_DETECTOR
**Porta**: 8700  
**Descrição**: Localiza defensas metálicas e de concreto (barreiras laterais)

#### Endpoint
```
POST /analyze/
```

#### Parâmetros
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| file | File | Imagem para análise |

#### Exemplo de Requisição
```bash
curl -X POST "http://localhost:8700/analyze/" \
  -F "file=@imagem_lateral.jpg"
```

#### Exemplo de Resposta
```json
{
  "detections": [
    {
      "class": 0,
      "class_name": "defensa_metalica",
      "confidence": 0.93,
      "bbox": [50, 300, 800, 600],
      "area": 140000
    }
  ]
}
```

### 3.2 FASTAPI_GUARDRAIL_QUALITY
**Porta**: 8702  
**Descrição**: Analisa o estado de conservação e anomalias em defensas (VAE)

#### Endpoint
```
POST /analyze/
POST /analyze_v2/
POST /analyze_v3/
```

#### Parâmetros
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| file | File | Imagem completa |
| x_min | int | Coordenada X mínima da bbox |
| y_min | int | Coordenada Y mínima da bbox |
| x_max | int | Coordenada X máxima da bbox |
| y_max | int | Coordenada Y máxima da bbox |

#### Exemplo de Requisição
```bash
curl -X POST "http://localhost:8702/analyze/" \
  -F "file=@imagem.jpg" \
  -F "x_min=100" \
  -F "y_min=200" \
  -F "x_max=500" \
  -F "y_max=600"
```

#### Exemplo de Resposta
```json
{
  "reconstruction_error": 0.034,
  "is_anomaly": false,
  "quality": "boa",
  "threshold": 0.05
}
```

### 3.3 FASTAPI_GUARDRAIL_SEGMENTER
**Porta**: 8703  
**Descrição**: Segmentação de alta precisão para cálculo de área de defensas (SAM)

#### Endpoint
```
POST /analyze/
```

#### Parâmetros
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| file | File | Imagem |
| x_min | int | Bbox X mínimo |
| y_min | int | Bbox Y mínimo |
| x_max | int | Bbox X máximo |
| y_max | int | Bbox Y máximo |

#### Exemplo de Requisição
```bash
curl -X POST "http://localhost:8703/analyze/" \
  -F "file=@defensa.jpg" \
  -F "x_min=100" \
  -F "y_min=200" \
  -F "x_max=500" \
  -F "y_max=600"
```

#### Exemplo de Resposta
```json
{
  "mask": "base64_encoded_mask",
  "area": 45000,
  "confidence": 0.95,
  "polygon": [[x1,y1], [x2,y2], ...]
}
```

---

## 4. Elementos de Drenagem

### 4.1 FASTAPI_DRAINAGE_DETECTOR
**Porta**: 8035  
**Descrição**: Detecção de bueiros, fendas e galerias de drenagem

#### Endpoints
```
POST /drainage-detect     (Detecção)
POST /drainage-classify   (Classificação de qualidade)
```

#### Exemplo de Detecção
```bash
curl -X POST "http://localhost:8035/drainage-detect/" \
  -F "file=@lateral_camera.jpg"
```

#### Resposta de Detecção
```json
{
  "results": [
    {
      "class": "bueiro",
      "xyxy": [120, 450, 280, 620],
      "confidence": 0.89
    }
  ]
}
```

#### Exemplo de Classificação
```bash
curl -X POST "http://localhost:8035/drainage-classify/" \
  -F "file=@bueiro_crop.jpg"
```

#### Resposta de Classificação
```json
{
  "result": "Bom",
  "quality_score": 0.85
}
```

### 4.2 FASTAPI_OUTFLOW_DETECTOR
**Porta**: 8421  
**Descrição**: Detecção de saídas de água e drenagem superficial lateral

#### Endpoints
```
POST /outflow-detect/
POST /outflow-classify/
```

#### Exemplo de Detecção
```bash
curl -X POST "http://localhost:8421/outflow-detect/" \
  -F "file=@lateral_camera.jpg"
```

#### Resposta
```json
{
  "results": [
    {
      "class": "saida_agua",
      "xyxy": [300, 400, 450, 580],
      "confidence": 0.91
    }
  ]
}
```

---

## 5. Sinalização Horizontal

### 5.1 FASTAPI_HORIZONTAL_MARKING_ANALYST
**Porta**: 8024  
**Descrição**: Segmentação e análise de desgaste da sinalização no asfalto

#### Classes de Sinalização Identificadas
- `1`: Continua
- `2`: Segmentada
- `3`: Legenda
- `4`: Zebrado

#### Qualidade
- Resultado de classificação: `boa` ou `ruim`

#### Endpoints
```
POST /horizontal-segment   (Segmentação das 4 classes)
POST /horizontal-classify  (Classificação de qualidade: boa/ruim)
```

#### Exemplo de Segmentação
```bash
curl -X POST "http://localhost:8024/horizontal-segment/" \
  -F "file=@pavimento.jpg"
```

#### Resposta de Segmentação
```json
{
  "masks": [
    {
      "class_id": 1,
      "class_name": "Continua",
      "polygon": [[x1,y1], [x2,y2], ...],
      "area": 25000
    }
  ]
}
```

#### Exemplo de Classificação
```bash
curl -X POST "http://localhost:8024/horizontal-classify/" \
  -F "file=@faixa_crop.jpg"
```

#### Resposta de Classificação
```json
{
  "quality": "boa"
}
```

---

## 6. Vegetação

### 6.1 FASTAPI_VEGETATION_CUBE_ANALYST
**Porta**: 8500  
**Descrição**: Classificação de altura de vegetação em imagens Cubemap (laterais)

#### Endpoint
```
POST /analyze/
```

#### Parâmetros
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| file | File | Imagem para análise |

#### Exemplo de Requisição
```bash
curl -X POST "http://localhost:8500/analyze/" \
  -F "file=@cube_image.jpg"
```

#### Exemplo de Resposta
```json
{
  "Score": 0.87,
  "Label": 1,
  "Classificação": "vegetacao_alta"
}
```

## 7. Geolocalização e GPS

### 7.1 FASTAPI_GEO_GPS_PREDICTOR
**Porta**: 8011  
**Descrição**: Calcula coordenadas GPS baseadas na profundidade e posição na imagem

#### Endpoint
```
POST /predict/
```

#### Parâmetros
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| lat | float | Latitude da imagem |
| lon | float | Longitude da imagem |
| x1 | float | Bbox X1 |
| y1 | float | Bbox Y1 |
| x2 | float | Bbox X2 |
| y2 | float | Bbox Y2 |
| cls | int | Classe do objeto detectado |

#### Exemplo de Requisição
```bash
curl -X POST "http://localhost:8011/predict/" \
  -F "lat=-15.598900" \
  -F "lon=-56.094900" \
  -F "x1=100" \
  -F "y1=150" \
  -F "x2=300" \
  -F "y2=400" \
  -F "cls=0"
```

#### Exemplo de Resposta
```json
{
  "dlat": "0.000123456789012",
  "dlon": "-0.000234567890123"
}
```

## 8. Informações Geoespaciais

### 8.1 GEOMETRIES
**Descrição**: Serviço para inserir geometrias de defensas no banco

**Execução**: Roda automaticamente ao iniciar, não possui API REST

---

## 🔌 Infraestrutura

### RabbitMQ
**Portas**: 5673 (AMQP), 15673 (Management)  
**Web UI**: http://localhost:15673  
**Credenciais**: rdt / 123456

#### Filas Disponíveis
- `Placa` - Processamento de placas
- `Matinho` - Processamento de vegetação
- `Horizontal` - Sinalização horizontal
- `DrenagemSuperficial` - Elementos de drenagem
- `Defensas` - Defensas metálicas e concreto
- `PGR` - Processamento PGR

### PostgreSQL + PostGIS
**Porta Desenvolvimento**: 1111 (ou `${SQL_PORT}`)  
**Credenciais**: myuser / mypassword  
**Database**: mydatabase

#### Principais Tabelas
- `trips` - Viagens
- `image_data` - Dados de imagens
- `plate_details` - Detalhes de placas
- `guardrail_details` - Detalhes de defensas
- `drainage_details` - Elementos de drenagem
- `horizontal_markings` - Sinalização horizontal

---

## 📝 Notas de Uso

### Headers Comuns
```
Content-Type: multipart/form-data
```

### Formatos de Imagem Aceitos
- JPEG (.jpg, .jpeg)
- PNG (.png)

### Limites
- Tamanho máximo de imagem: ~10MB (varia por API)
- Timeout padrão: 300 segundos

### Versionamento
APIs versionadas usam prefixo `/v{major}/` ou `/v{major}_{minor}/`
- Exemplo: `/v1/endpoint/` ou `/v1_0/endpoint/`
- Use `/latest/endpoint/` para última versão

---

## 🔍 Testes Rápidos

### Script de Teste de Todas as APIs
```bash
#!/bin/bash

echo "=== Testando APIs ==="

# New Trip
curl -s http://localhost:8013/docs > /dev/null && echo "✓ New Trip (8013)" || echo "✗ New Trip (8013)"

# Sign Detection
curl -s http://localhost:8010/docs > /dev/null && echo "✓ Sign Detection (8010)" || echo "✗ Sign Detection (8010)"

# GPS Predict
curl -s http://localhost:8011/docs > /dev/null && echo "✓ GPS Predict (8011)" || echo "✗ GPS Predict (8011)"

# Sign Quality Classification
curl -s http://localhost:8016/docs > /dev/null && echo "✓ Sign Class (8016)" || echo "✗ Sign Class (8016)"

# Tracker
curl -s http://localhost:8714/docs > /dev/null && echo "✓ Tracker (8714)" || echo "✗ Tracker (8714)"

# Defensa Detection
curl -s http://localhost:8700/docs > /dev/null && echo "✓ Defensa (8700)" || echo "✗ Defensa (8700)"

# Defensa VAE
curl -s http://localhost:8702/docs > /dev/null && echo "✓ Defensa VAE (8702)" || echo "✗ Defensa VAE (8702)"

# SAM
curl -s http://localhost:8703/docs > /dev/null && echo "✓ SAM (8703)" || echo "✗ SAM (8703)"

# Horizontal
curl -s http://localhost:8024/docs > /dev/null && echo "✓ Horizontal (8024)" || echo "✗ Horizontal (8024)"

# Vegetação
curl -s http://localhost:8500/docs > /dev/null && echo "✓ Vegetação (8500)" || echo "✗ Vegetação (8500)"

# Drainage
curl -s http://localhost:8035/docs > /dev/null && echo "✓ Drainage (8035)" || echo "✗ Drainage (8035)"

# Outflow
curl -s http://localhost:8421/docs > /dev/null && echo "✓ Outflow (8421)" || echo "✗ Outflow (8421)"

echo "=== Fim dos Testes ==="
```

### Documentação Interativa (Swagger)
Cada API possui documentação interativa em `/docs`
- Exemplo: http://localhost:8010/docs

---

**Última atualização**: Março 2026  
**Para mais informações**: Consulte README.md e COMANDOS_COMPLETOS.md
