# RoadSense Infrastructure - Referência de APIs

## 📋 Índice de APIs

- [1. Gerenciamento de Viagens](#1-gerenciamento-de-viagens)
- [2. Detecção e Classificação de Placas](#2-detecção-e-classificação-de-placas)
- [3. Análise de Defensas](#3-análise-de-defensas)
- [4. Elementos de Drenagem](#4-elementos-de-drenagem)
- [5. Sinalização Horizontal](#5-sinalização-horizontal)
- [6. Vegetação](#6-vegetação)
- [7. Geolocalização e GPS](#7-geolocalização-e-gps)
- [8. Qualidade e Pavimento](#8-qualidade-e-pavimento)
- [9. Informações Geoespaciais](#9-informações-geoespaciais)

---

## 1. Gerenciamento de Viagens

### 1.1 FASTAPI_GET_NEW_TRIP
**Porta**: 8013  
**Descrição**: Cria uma nova viagem no sistema e retorna o ID único

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

### 2.1 FASTAPI_SIGN_DETECTION
**Porta**: 8010  
**Descrição**: Detecção de placas e elementos viários em imagens

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

### 2.2 FASTAPI_SIGN_CLASSIFICATION
**Porta**: 8016  
**Descrição**: Classificação detalhada de placas de trânsito

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
  "class_id": 5,
  "class_name": "velocidade_maxima_80",
  "confidence": 0.98,
  "quality": "boa"
}
```

### 2.3 FASTAPI_NUMERIC_OCR
**Porta**: 8014  
**Descrição**: Extração de números de placas quilométricas usando OCR

#### Endpoint
```
POST /v1_0/ocr/get_km
```

#### Parâmetros
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| file | File | Imagem da placa KM |

#### Exemplo de Requisição
```bash
curl -X POST "http://localhost:8014/v1_0/ocr/get_km" \
  -F "file=@placa_km.jpg"
```

#### Exemplo de Resposta
```json
{
  "km_number": "345",
  "confidence": 0.92,
  "text_detected": "KM 345"
}
```

### 2.4 FASTAPI_CLASSIFY_KM_PLATES
**Porta**: 8015  
**Descrição**: Classificação de tipo de placa quilométrica (azul/branca)

#### Endpoint
```
POST /v1_0/classify
```

#### Exemplo de Requisição
```bash
curl -X POST "http://localhost:8015/v1_0/classify" \
  -F "file=@placa.jpg"
```

#### Exemplo de Resposta
```json
{
  "class": 0,
  "type": "placa_azul"
}
```

---

## 3. Análise de Defensas

### 3.1 FASTAPI_DEFENSA_DETECTION
**Porta**: 8700  
**Descrição**: Detecção automática de defensas metálicas e de concreto

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

### 3.2 FASTAPI_DEFENSA_VAE
**Porta**: 8702  
**Descrição**: Análise de qualidade de defensas usando VAE (Variational Autoencoder)

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

### 3.3 FASTAPI_SAM
**Porta**: 8703  
**Descrição**: Segmentação precisa de defensas usando Segment Anything Model

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

### 4.1 FASTAPI_DRAINAGE_DETECTION
**Porta**: 8035  
**Descrição**: Detecção automática de elementos de drenagem (bueiros, galerias)

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

### 4.2 FASTAPI_OUTFLOW_DETECTION
**Porta**: 8421  
**Descrição**: Detecção de saídas de água e elementos de drenagem superficial
#### Exemplo de Detecção
```bash
curl -X POST "http://localhost:8421/analyze/" \

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

### 5.1 FASTAPI_HORIZONTAL_SIGNAGE
**Porta**: 8024  
**Descrição**: Detecção e classificação de sinalização horizontal (faixas, zebras, etc)

#### Endpoints
```
POST /horizontal-segment   (Segmentação)
POST /horizontal-classify  (Classificação)
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
      "class_id": 0,
      "class_name": "faixa_continua",
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
  "quality": "boa",
  "visibility": 0.92,
  "degradation_level": "baixo"
}
```

---

## 6. Vegetação

### 6.1 FASTAPI_VEGETACAO_CUBE
**Porta**: 8500  
**Descrição**: Classificação de vegetação em imagens do tipo cubemap

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

### 6.2 FASTAPI_VEGETACAO_CLASSIFICATION
**Porta**: 8400  
**Descrição**: Classificação de níveis de vegetação (Alta, Baixa, Média)

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
curl -X POST "http://localhost:8400/analyze/" \
  -F "file=@imagem.jpg"
```

#### Exemplo de Resposta
```json
{
  "Score": 0.95,
  "Label": 0,
  "Classificação": "Vegetação_alta"
}
```

---

## 7. Geolocalização e GPS

### 7.1 FASTAPI_GPS_PREDICT
**Porta**: 8011  
**Descrição**: Predição de coordenadas GPS precisas baseado em bounding boxes

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

### 7.2 FASTAPI_BRIDGE_PREDICT
**Porta**: 8018  
**Descrição**: Verifica se coordenadas estão próximas a uma ponte

#### Endpoint
```
POST /v1/bridge-exists/
```

#### Exemplo
```bash
curl -X POST "http://localhost:8018/v1/bridge-exists/" \
  -F "lat=-15.5989" \
  -F "lon=-56.0949"
```

#### Resposta
```json
{
  "is bridge": "true"
}
```

### 7.3 FASTAPI_CANTEIRO_PREDICT
**Porta**: 8017  
**Descrição**: Detecta presença de canteiro central

#### Endpoint
```
POST /v1/median-exists/
POST /v2/median-exists/
POST /v3/median-exists/
```

### 7.4 FASTAPI_PRF_PREDICT
**Porta**: 8019  
**Descrição**: Verifica proximidade de postos da PRF

#### Endpoint
```
POST /v1/prf-exists/
```

### 7.5 FASTAPI_NS_PREDICT
**Porta**: 8020  
**Descrição**: Determina orientação (Norte/Sul)

#### Endpoint
```
POST /v1/north-or-south/
```

### 7.6 FASTAPI_GET_HIGHWAY_NUMBER
**Porta**: 8021  
**Descrição**: Retorna número da rodovia baseado em coordenadas

#### Endpoint
```
POST /v1/get-highway-number/
```

### 7.7 FASTAPI_KM_NEAREST
**Porta**: 8023  
**Descrição**: Encontra quilômetro mais próximo

#### Endpoint
```
GET /latest/get_segment_km?trip_id=1&lat=-15.5989&lon=-56.0949
```

---

## 8. Qualidade e Pavimento

### 8.1 FASTAPI_QUALIDADE
**Porta**: 8330  
**Descrição**: Análise de qualidade geral de elementos

#### Endpoints
```
POST /v1/qualidade/  (múltiplas imagens)
POST /v2/qualidade/  (arquivo zip)
```

#### Exemplo v1
```bash
curl -X POST "http://localhost:8330/v1/qualidade/" \
  -F "files=@img1.jpg" \
  -F "files=@img2.jpg"
```

#### Exemplo v2
```bash
curl -X POST "http://localhost:8330/v2/qualidade/" \
  -F "zip_file=@imagens.zip"
```

### 8.2 FASTAPI_PAVIMENTO_DETECTION
**Porta**: 8310  
**Descrição**: Detecção de patologias e defeitos no pavimento (buracos, trincas)

#### Endpoint
```
POST /analyze/
```

---

## 9. Informações Geoespaciais

### 9.1 FASTAPI_PLOT_COORDS_MATO
**Porta**: 8022  
**Descrição**: Visualização de coordenadas em mapa

#### Endpoint
```
GET /v3/plot-coords-mato/
```

#### Resposta
```html
<!-- Retorna HTML com mapa interativo -->
```

### 9.2 GEOMETRIES
**Descrição**: Serviço para inserir geometrias de defensas no banco

**Execução**: Roda automaticamente ao iniciar, não possui API REST

---

## 🔌 Infraestrutura

### RabbitMQ
**Portas**: 5672 (AMQP), 15672 (Management)  
**Web UI**: http://localhost:15672  
**Credenciais**: rdt / 123456

#### Filas Disponíveis
- `Placa` - Processamento de placas
- `Matinho` - Processamento de vegetação
- `Horizontal` - Sinalização horizontal
- `DrenagemSuperficial` - Elementos de drenagem
- `Defensas` - Defensas metálicas e concreto
- `PGR` - Processamento PGR

### PostgreSQL + PostGIS
**Porta Desenvolvimento**: 5433  
**Porta Produção**: 5555  
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

# Sign Classification
curl -s http://localhost:8016/docs > /dev/null && echo "✓ Sign Class (8016)" || echo "✗ Sign Class (8016)"

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

**Última atualização**: Novembro 2024  
**Para mais informações**: Consulte README.md e COMANDOS_COMPLETOS.md
