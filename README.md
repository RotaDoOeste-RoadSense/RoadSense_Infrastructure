# RoadSense Infrastructure - Documentação Completa

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Arquitetura do Sistema](#arquitetura-do-sistema)
- [Estrutura do Repositório](#estrutura-do-repositório)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e Configuração](#instalação-e-configuração)
- [APIs Disponíveis](#apis-disponíveis)
- [Banco de Dados](#banco-de-dados)
- [Fluxo de Trabalho](#fluxo-de-trabalho)
- [Guia de Uso](#guia-de-uso)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Sobre o Projeto

### RDT – Recurso de Desenvolvimento Tecnológico

Projeto desenvolvido pela **Concessionária Nova Rota do Oeste** para criar tecnologias avançadas de identificação e avaliação automatizada de defeitos em pavimentos e elementos viários usando Inteligência Artificial (IA).

### Objetivos Principais

#### 1. Processamento Automático do IGG e ICP com IA
- Desenvolvimento de tecnologia nacional para levantamento automático de defeitos superficiais
- Utilização do Levantamento Visual Contínuo Informatizado (LVCI)
- Treinamento de modelos de IA especializados
- Interface amigável para visualização de resultados

#### 2. Monitoramento Inteligente de Elementos Viários
- Identificação, georreferenciamento e cadastro automático de elementos na faixa de domínio
- Avaliação automatizada do estado de conservação
- Validação e comparação com métodos convencionais

---

## 🏗️ Arquitetura do Sistema

### Visão Geral

O sistema utiliza uma **arquitetura de microserviços** baseada em containers Docker, oferecendo:

- ✅ **Escalabilidade Horizontal**: Fácil adição de novos serviços
- ✅ **Isolamento de Falhas**: Problemas em um serviço não afetam outros
- ✅ **Flexibilidade**: Adaptável a diferentes rodovias, estados e empresas
- ✅ **GPU Acceleration**: Uso otimizado de GPUs NVIDIA para inferência

### Componentes Principais

```
┌─────────────────────────────────────────────────────────┐
│                    RabbitMQ (Broker)                    │
│            Gerenciamento de Filas de Tarefas            │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   PostgreSQL  │  │  APIs FastAPI │  │ Fluxo Sistema │
│   + PostGIS   │  │ (Microserviços)│  │  (Workers)    │
└───────────────┘  └───────────────┘  └───────────────┘
```

### Tecnologias Utilizadas

- **Backend**: FastAPI, Python 3.9+
- **Banco de Dados**: PostgreSQL + PostGIS (dados geoespaciais)
- **Message Broker**: RabbitMQ
- **Containerização**: Docker & Docker Compose
- **IA/ML**: 
  - YOLOv8 (detecção de objetos)
  - TensorRT (otimização de inferência)
  - SAM (Segment Anything Model)
  - VAE (Variational Autoencoder)
  - Redes Neurais customizadas
- **GPU**: NVIDIA CUDA 12.6, cuDNN
- **Geoespacial**: GeoPandas, Shapely, GeoAlchemy2

---

## 📁 Estrutura do Repositório

```
RoadSense_Infrastructure/
│
├── APIs/                              # Todos os microserviços
│   ├── docker-compose.yml             # Configuração de desenvolvimento
│   ├── docker-compose-prod.yml        # Configuração de produção
│   ├── start.sh                       # Script para iniciar serviços
│   ├── stop.sh                        # Script para parar serviços
│   ├── remove.sh                      # Script para remover containers e volumes
│   │
│   ├── rabbitmq/                      # Message Broker
│   │   ├── Dockerfile
│   │   ├── rabbitmq.conf
│   │   └── definitions.json
│   │
│   ├── SQL/                           # Banco de dados PostgreSQL
│   │   ├── Dockerfile
│   │   └── scripts/
│   │       ├── bruna.sql              # Schema principal
│   │       └── victor.sql             # Schema adicional
│   │
│   ├── GEOMETRIES/                    # Dados geométricos
│   │   ├── Dockerfile
│   │   ├── insert_geometries.py
│   │   ├── concreto/                  # Geometrias de defensas concreto
│   │   └── metal/                     # Geometrias de defensas metal
│   │
│   ├── NoSQL/                         # MongoDB (opcional)
│   │
│   ├── FASTAPI_GET_NEW_TRIP/          # Criação de novas viagens
│   ├── FASTAPI_GPS_PREDICT/           # Predição de coordenadas GPS
│   ├── FASTAPI_YOLO_IMAGE/            # Detecção de placas com YOLO
│   ├── FASTAPI_SIGN_CLASSIFICATION/   # Classificação de placas
│   ├── FASTAPI_NUMERIC_OCR/           # OCR para números de KM
│   ├── FASTAPI_CLASSIFY_KM_PLATES/    # Classificação de placas KM
│   ├── FASTAPI_DEFENSA/               # Detecção de defensas (YOLO)
│   ├── FASTAPI_DEFENSA_VAE/           # Análise de qualidade defensas (VAE)
│   ├── FASTAPI_SAM/                   # Segmentação com SAM
│   ├── FASTAPI_HORIZONTAL_SIGNAGE/    # Sinalização horizontal
│   ├── FASTAPI_VEGETACAO_YOLO_CUBE/   # Detecção de vegetação
│   ├── FASTAPI_YOLO_DRAINAGE/         # Detecção de drenagem
│   ├── FASTAPI_YOLO_OUTFLOW/          # Detecção de saídas de água
│   ├── FASTAPI_QUALIDADE/             # Análise de qualidade geral
│   ├── FASTAPI_BRIDGE_PREDICT/        # Detecção de pontes
│   ├── FASTAPI_CANTEIRO_PREDICT/      # Detecção de canteiros centrais
│   ├── FASTAPI_PRF_PREDICT/           # Proximidade de postos PRF
│   ├── FASTAPI_NS_PREDICT/            # Orientação Norte/Sul
│   ├── FASTAPI_GET_HIGHWAY_NUMBER/    # Número da rodovia
│   ├── FASTAPI_KM_NEAREST/            # KM mais próximo
│   ├── FASTAPI_PLOT_COORDS_MATO/      # Visualização de coordenadas
│   ├── FASTAPI_TRECHO_PREDICT/        # Predição de trechos
│   ├── FASTAPI_YOLO_PAVIMENTO/        # Análise de pavimento
│   ├── FASTAPI_YOLO_IMAGE_TENSORRT/   # YOLO otimizado com TensorRT
│   └── FASTAPI_YOLO_IMAGE_TRUCK/      # Detecção de caminhões
│
├── Fluxo_sistema/                     # Sistema de processamento
│   ├── Dockerfile                     # Container do fluxo
│   ├── requirements.txt               # Dependências Python
│   ├── config.yml                     # Configurações gerais
│   ├── main.py                        # Script principal de envio de tarefas
│   ├── main_pgr.py                    # Script para processamento PGR
│   ├── up_disciplines.py              # Workers de processamento
│   ├── receber_nova_trip.py           # Criação de nova viagem
│   ├── utils.py                       # Utilitários gerais
│   ├── utils_pgr.py                   # Utilitários PGR
│   ├── database_models.py             # Modelos do banco de dados
│   ├── build.sh                       # Build do container
│   ├── run_container.sh               # Execução do container
│   │
│   ├── Placas/                        # Módulo de placas
│   │   ├── __main__.py
│   │   ├── encontrar_todas_placas.py
│   │   ├── encontrar_gps_todas_placas.py
│   │   └── analyze_plate_quality.py
│   │
│   ├── Defensa/                       # Módulo de defensas
│   ├── Drenagem/                      # Módulo de drenagem
│   ├── Horizontal/                    # Módulo de sinalização horizontal
│   ├── Vegetacao/                     # Módulo de vegetação
│   ├── jsons/                         # Dados JSON de viagens
│   └── trips/                         # Dados de viagens
│
├── README.md                          # Documentação original
├── README_ATUALIZADO.md               # Esta documentação
└── Git Branching.md                   # Estratégia de versionamento
```

---

## 🔧 Pré-requisitos

### Hardware

- **GPU NVIDIA**: Recomendado GTX 1080 Ti ou superior
- **RAM**: Mínimo 32GB, recomendado 64GB
- **Armazenamento**: Mínimo 500GB SSD (para dados e modelos)
- **CPU**: 8+ cores recomendado

### Software

- **Sistema Operacional**: Linux (Ubuntu 20.04)
- **Docker**: Versão 24.0+
- **Docker Compose**: Versão 2.0+
- **NVIDIA Docker Runtime**: Para suporte a GPU
- **NVIDIA Drivers**: Versão 525+ para CUDA 12.6

### Verificação de Instalação

```bash
# Verificar Docker
docker --version

# Verificar Docker Compose
docker compose version

# Verificar GPU NVIDIA
nvidia-smi

# Verificar NVIDIA Docker Runtime
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi
```

---

## 🚀 Instalação e Configuração

### 1. Clonar o Repositório

```bash
git clone https://github.com/RotaDoOeste-RoadSense/RoadSense_Infrastructure.git
cd RoadSense_Infrastructure
```

### 2. Configurar Variáveis de Ambiente

#### Banco de Dados (SQL)
Edite o arquivo `APIs/SQL/Dockerfile` se necessário:
```env
POSTGRES_DB=mydatabase
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
```

#### RabbitMQ
Edite o arquivo `APIs/docker-compose.yml`:
```env
RABBITMQ_DEFAULT_USER=rdt
RABBITMQ_DEFAULT_PASS=123456
```

### 3. Configurar Fluxo do Sistema

Edite `Fluxo_sistema/config.yml`:

```yaml
database:
  url: "postgresql://myuser:mypassword@127.0.0.1:5433/mydatabase"

paths:
  root: "/caminho/para/seus/dados/"

# URLs das APIs (manter localhost se rodando localmente)
inference:
  url: "http://127.0.0.1:8010/analyze/"
# ... outras configurações
```

### 4. Iniciar os Serviços

```bash
cd APIs

# Iniciar em modo desenvolvimento
docker compose up --build -d

# OU iniciar em modo produção + desenvolvimento
./start.sh
```

### 5. Verificar Status dos Serviços

```bash
# Listar containers em execução
docker compose ps

# Ver logs de todos os serviços
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f fastapi_yolo

# Verificar saúde do RabbitMQ
curl http://localhost:15672
# Login: rdt / 123456
```

### 6. Configurar Workers de Processamento

```bash
cd Fluxo_sistema

# Build do container
./build.sh

# Executar container com workers
./run_container.sh

# Dentro do container, iniciar os workers
python up_disciplines.py
```

---

## 🔌 APIs Disponíveis

### Portas e Endpoints

| Serviço | Porta | Endpoint Principal | Descrição |
|---------|-------|-------------------|-----------|
| **RabbitMQ** | 5672, 15672 | http://localhost:15672 | Gerenciamento de filas |
| **PostgreSQL** | 5433 | localhost:5433 | Banco de dados principal |
| **PostgreSQL Prod** | 5555 | localhost:5555 | Banco de dados produção |
| **YOLO Image** | 8010 | POST /analyze/ | Detecção de placas |
| **GPS Predict** | 8011 | POST /predict/ | Predição GPS |
| **New Trip** | 8013 | POST /new-trip/ | Criar nova viagem |
| **Numeric OCR** | 8014 | POST /v1_0/ocr/get_km | OCR números KM |
| **Classify KM Plates** | 8015 | POST /v1_0/classify | Classificar placas KM |
| **Sign Classification** | 8016 | POST /plate-inference/ | Classificar placas |
| **Defensa YOLO** | 8700 | POST /analyze/ | Detecção defensas |
| **Defensa VAE** | 8702 | POST /analyze/ | Qualidade defensas |
| **Defensa SAM** | 8703 | POST /analyze/ | Segmentação defensas |
| **Horizontal Signage** | 8024 | POST /horizontal-segment/ | Sinalização horizontal |
| **Vegetação Cube** | 8500 | POST /analyze/ | Análise vegetação |
| **Qualidade** | 8330 | POST /qualidade/ | Análise qualidade |
| **Drainage** | 8035 | POST /drainage-detect/ | Detecção drenagem |
| **Outflow** | 8421 | POST /outflow-detect/ | Detecção saídas água |

### Exemplos de Uso das APIs

#### 1. Criar Nova Viagem

```bash
curl -X POST "http://localhost:8013/new-trip/" \
  -F "path=/mnt/hd1/Extracoes/VIAGEM_001" \
  -F "way=N" \
  -F "starting_city=Rondonópolis" \
  -F "ending_city=Cuiabá" \
  -F "production=false"
```

Resposta:
```json
{
  "trip_id": 1,
  "message": "Trip created successfully"
}
```

#### 2. Análise de Imagem com YOLO

```bash
curl -X POST "http://localhost:8010/analyze/" \
  -F "file=@/path/to/image.jpg" \
  -F "classes=0,1,2"
```

Resposta:
```json
{
  "detections": [
    {
      "class": 0,
      "class_name": "placa_km",
      "confidence": 0.95,
      "bbox": [100, 150, 300, 400]
    }
  ]
}
```

#### 3. Predição de GPS

```bash
curl -X POST "http://localhost:8011/predict/" \
  -F "lat=-15.5989" \
  -F "lon=-56.0949" \
  -F "x1=100" \
  -F "y1=150" \
  -F "x2=300" \
  -F "y2=400" \
  -F "cls=0"
```

#### 4. Detecção de Defensas

```bash
curl -X POST "http://localhost:8700/analyze/" \
  -F "file=@/path/to/image.jpg"
```

#### 5. Análise de Qualidade (Defensas)

```bash
curl -X POST "http://localhost:8702/analyze/" \
  -F "file=@/path/to/image.jpg" \
  -F "x_min=100" \
  -F "y_min=150" \
  -F "x_max=300" \
  -F "y_max=400"
```

---

## 🗄️ Banco de Dados

### Estrutura das Tabelas Principais

#### trips
Armazena informações sobre cada viagem/extração
```sql
CREATE TABLE trips (
  trip_id SERIAL PRIMARY KEY,
  root_folder VARCHAR(2000),
  timestamp TIMESTAMP,
  way VARCHAR(20),          -- 'N' ou 'S'
  starting_city VARCHAR(200),
  ending_city VARCHAR(200)
);
```

#### image_data
Dados de cada imagem capturada
```sql
CREATE TABLE image_data (
  image_id SERIAL PRIMARY KEY,
  image_name VARCHAR(200),
  latitude DECIMAL(18,15),
  longitude DECIMAL(18,15),
  timestamp INT,
  "order" BIGINT,
  trip_id INT REFERENCES trips(trip_id)
);
```

#### plate_details
Detalhes de placas detectadas
```sql
CREATE TABLE plate_details (
  plate_details_id SERIAL PRIMARY KEY,
  class_value FLOAT,
  class_name VARCHAR(30),
  prob FLOAT,
  x1 FLOAT, y1 FLOAT, x2 FLOAT, y2 FLOAT,
  status SMALLINT,
  side VARCHAR(1),
  all_plates_matched_id INT
);
```

#### guardrail_details
Detalhes de defensas detectadas
```sql
CREATE TABLE guardrail_details (
  guardrail_details_id SERIAL PRIMARY KEY,
  class_value SMALLINT,
  class_name VARCHAR(30),
  score FLOAT,
  cam SMALLINT,
  geom GEOMETRY(Point, 4326),
  x1 FLOAT, y1 FLOAT, x2 FLOAT, y2 FLOAT,
  image_id INT REFERENCES image_data(image_id),
  guardrail_geometry_id INT,
  outlier BOOLEAN,
  reconstruction_error FLOAT
);
```

#### drainage_details
Detalhes de elementos de drenagem
```sql
CREATE TABLE drainage_details (
  drainage_details_id SERIAL PRIMARY KEY,
  detection_type VARCHAR(50),  -- 'drainage' ou 'outflow'
  x1 FLOAT, y1 FLOAT, x2 FLOAT, y2 FLOAT,
  cam SMALLINT,
  quality_value SMALLINT,
  geom GEOMETRY(Point, 4326),
  image_id INT REFERENCES image_data(image_id)
);
```

#### horizontal_markings
Sinalização horizontal
```sql
CREATE TABLE horizontal_markings (
  horizontal_markings_id SERIAL PRIMARY KEY,
  class_id SMALLINT,
  class_name CHAR(20),
  mask_polygon TEXT,
  quality_score REAL,
  image_id INT REFERENCES image_data(image_id)
);
```

### Conexão ao Banco

```python
from sqlalchemy import create_engine

# Desenvolvimento
DATABASE_URL = "postgresql://myuser:mypassword@localhost:5433/mydatabase"

# Produção
DATABASE_URL_PROD = "postgresql://myuser:mypassword@localhost:5555/mydatabase"

engine = create_engine(DATABASE_URL)
```

---

## 🔄 Fluxo de Trabalho

### Visão Geral do Pipeline

```
1. Captura de Imagens
        ↓
2. Criação de Viagem (trip_id)
        ↓
3. Importação de Dados GPS
        ↓
4. Envio de Tarefas para RabbitMQ
        ↓
5. Processamento por Workers
        ↓
6. Inferência com APIs
        ↓
7. Armazenamento no Banco
        ↓
8. Visualização e Análise
```

### 1. Preparar Dados da Viagem

Organize seus dados na seguinte estrutura:
```
/mnt/hd1/Extracoes/VIAGEM_001/
├── Cube/              # Imagens em formato cube
│   ├── image_0001_1.jpg
│   ├── image_0001_2.jpg
│   └── ...
├── GPS_data.xlsx      # Dados GPS (opcional)
└── jsons/            # Metadados JSON (opcional)
```

### 2. Criar Nova Viagem

```python
# No container Fluxo_sistema
import receber_nova_trip

folder = "/mnt/hd1/Extracoes/VIAGEM_001"
trip_direction = 'N'  # ou 'S'

trip_id = receber_nova_trip.main(folder, trip_direction)
print(f"Trip ID criado: {trip_id}")
```

### 3. Importar Dados GPS (Opcional)

```python
from utils import run as import_gps

trip_id = 1
gps_file = 'trips/GPS_norte.xlsx'
import_gps(trip_id, gps_file)
```

### 4. Importar Dados de JSONs (Opcional)

```python
from utils import run_json_folder

trip_id = 1
json_folder = 'jsons/'
run_json_folder(trip_id, json_folder)
```

### 5. Enviar Tarefas para Processamento

Edite `Fluxo_sistema/main.py`:

```python
folder = "/mnt/hd1/Extracoes/VIAGEM_001"
trip_id = 1
trip_direction = 'N'

# Enviar para todas as filas
for queue in ['Placa', 'Matinho', 'Horizontal', 'DrenagemSuperficial', 'Defensas']:
    connection = connect_to_rabbit()
    channel = connection.channel()
    send_task(queue, {
        "trip_id": trip_id,
        "trip_direction": trip_direction,
        "folder": folder
    })
    connection.close()
```

Execute:
```bash
python main.py
```

### 6. Processar com Workers

Em outro terminal dentro do container:

```bash
python up_disciplines.py
```

Os workers irão:
1. Consumir tarefas do RabbitMQ
2. Carregar imagens
3. Chamar APIs de inferência
4. Salvar resultados no banco

### 7. Monitorar Processamento

#### Via RabbitMQ Management
```
http://localhost:15672
Login: rdt / 123456
```

#### Via Logs
```bash
# No diretório Fluxo_sistema
docker logs fluxo -f
```

#### Via Banco de Dados
```python
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://myuser:mypassword@localhost:5433/mydatabase")

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM plate_details WHERE image_id IN (SELECT image_id FROM image_data WHERE trip_id = :trip_id)"), {"trip_id": 1})
    print(f"Placas detectadas: {result.scalar()}")
```

---

## 📖 Guia de Uso

### Cenário 1: Processar Nova Viagem Completa

```bash
# 1. Iniciar serviços
cd APIs
./start.sh

# 2. Aguardar inicialização (verificar logs)
docker compose logs -f rabbitmq

# 3. Preparar e executar fluxo
cd ../Fluxo_sistema
./run_container.sh

# Dentro do container:
# 4. Criar trip
python -c "import receber_nova_trip; print(receber_nova_trip.main('/mnt/dados/VIAGEM_001', 'N'))"

# 5. Editar main.py com trip_id retornado
nano main.py

# 6. Enviar tarefas
python main.py

# 7. Iniciar workers (em outro terminal do container)
python up_disciplines.py
```

### Cenário 2: Processar Apenas Uma Disciplina

```python
# Processar apenas placas
from Placas import run as processar_placas

folder = "/mnt/dados/VIAGEM_001"
trip_id = 1
trip_direction = 'N'

processar_placas(None, folder, trip_id, trip_direction)
```

### Cenário 3: Processar PGR (Point Grey Research)

```python
# Editar main_pgr.py
pgr_folder = '/mnt/dados/PGR_FOLDER'
frames_output_folder = '/mnt/dados/OUTPUT_FRAMES'

# Enviar tarefa
python main_pgr.py

# Workers processarão automaticamente
```

### Cenário 4: Reprocessar com Novos Modelos

```bash
# 1. Parar serviços
cd APIs
docker compose down

# 2. Atualizar modelos na API específica
# Exemplo: FASTAPI_DEFENSA/api_folder/weights/

# 3. Rebuild apenas a API afetada
docker compose build fastapi_defensa_yolo

# 4. Reiniciar serviços
docker compose up -d

# 5. Reprocessar dados específicos
# (Consultar banco, deletar registros antigos, reenviar tarefas)
```

---

## 🐛 Troubleshooting

### Problema: Container não inicia com GPU

**Sintoma**: Erro "could not select device driver"

**Solução**:
```bash
# Verificar NVIDIA Docker Runtime
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi

# Se falhar, reinstalar nvidia-docker2
sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### Problema: RabbitMQ não conecta

**Sintoma**: "Connection refused" em workers

**Solução**:
```bash
# Verificar se RabbitMQ está rodando
docker compose ps rabbitmq

# Ver logs
docker compose logs rabbitmq

# Reiniciar se necessário
docker compose restart rabbitmq

# Aguardar healthcheck passar
docker compose ps
```

### Problema: Banco de dados não aceita conexões

**Sintoma**: "Connection to database failed"

**Solução**:
```bash
# Verificar container
docker compose ps sql

# Testar conexão
docker exec -it <sql_container_id> psql -U myuser -d mydatabase

# Verificar logs
docker compose logs sql
```

### Problema: API retorna erro 500

**Sintoma**: Erro interno ao chamar API

**Solução**:
```bash
# Ver logs da API específica
docker compose logs fastapi_yolo

# Entrar no container para debug
docker exec -it <api_container_id> bash

# Testar manualmente
python
>>> from inference import get_plates
>>> # testar função
```

### Problema: Workers não processam tarefas

**Sintoma**: Tarefas ficam em "ready" no RabbitMQ

**Solução**:
```python
# Verificar se workers estão rodando
# No container fluxo_sistema
ps aux | grep python

# Verificar logs do worker
# Ver output de up_disciplines.py

# Restartar workers
# Ctrl+C e executar novamente
python up_disciplines.py
```

### Problema: Memória GPU esgotada

**Sintoma**: "CUDA out of memory"

**Solução**:
```bash
# Verificar uso de GPU
nvidia-smi

# Matar processos se necessário
# Ajustar batch_size nos modelos

# Reiniciar containers que usam GPU
docker compose restart fastapi_defensa_yolo fastapi_yolo
```

### Problema: Imagens não encontradas

**Sintoma**: FileNotFoundError ao processar

**Solução**:
```bash
# Verificar montagem de volumes
docker compose exec fluxo ls -la /mnt/

# Verificar permissões
ls -la /mnt/dados/VIAGEM_001/

# Ajustar docker-compose.yml se necessário
# Adicionar volume:
# - /seu/caminho:/mnt/seu/caminho
```

---

## 📊 Monitoramento e Logs

### Logs do Sistema

```bash
# Todos os serviços
docker compose logs -f

# Serviço específico com tail
docker compose logs -f --tail=100 fastapi_yolo

# Logs desde um horário
docker compose logs --since 2024-01-01T10:00:00
```

### Métricas RabbitMQ

Acesse: http://localhost:15672

- Visualizar filas
- Monitorar taxa de mensagens
- Ver conexões ativas
- Verificar uso de memória

### Monitoramento de GPU

```bash
# Uso atual
nvidia-smi

# Monitoramento contínuo
watch -n 1 nvidia-smi

# Logs de uso
nvidia-smi dmon
```

### Queries Úteis do Banco

```sql
-- Total de imagens por viagem
SELECT trip_id, COUNT(*) 
FROM image_data 
GROUP BY trip_id;

-- Placas detectadas por viagem
SELECT t.trip_id, COUNT(pd.plate_details_id)
FROM trips t
JOIN image_data id ON t.trip_id = id.trip_id
JOIN all_plates_matched apm ON id.image_id = apm.image_id
JOIN plate_details pd ON apm.all_plates_matched_id = pd.all_plates_matched_id
GROUP BY t.trip_id;

-- Defensas por viagem
SELECT t.trip_id, COUNT(gd.guardrail_details_id)
FROM trips t
JOIN image_data id ON t.trip_id = id.trip_id
JOIN guardrail_details gd ON id.image_id = gd.image_id
GROUP BY t.trip_id;

-- Última viagem processada
SELECT * FROM trips ORDER BY trip_id DESC LIMIT 1;
```

---

## 🔒 Segurança e Boas Práticas

### Credenciais

⚠️ **IMPORTANTE**: Altere as credenciais padrão em produção!

```bash
# Banco de dados
POSTGRES_USER=<seu_usuario_seguro>
POSTGRES_PASSWORD=<senha_forte>

# RabbitMQ
RABBITMQ_DEFAULT_USER=<seu_usuario>
RABBITMQ_DEFAULT_PASS=<senha_forte>
```

### Backup do Banco de Dados

```bash
# Backup
docker exec <sql_container_id> pg_dump -U myuser mydatabase > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20240101.sql | docker exec -i <sql_container_id> psql -U myuser -d mydatabase
```

### Limpeza de Dados Antigos

```bash
# Remover volumes não utilizados
docker volume prune

# Remover imagens antigas
docker image prune -a

# Limpeza completa (CUIDADO!)
./remove.sh
```

---

## 📚 Recursos Adicionais

### Documentação das Tecnologias

- [FastAPI](https://fastapi.tiangolo.com/)
- [Docker](https://docs.docker.com/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [PostGIS](https://postgis.net/documentation/)
- [RabbitMQ](https://www.rabbitmq.com/documentation.html)
- [YOLOv8](https://docs.ultralytics.com/)

### Estratégia de Git

Consulte o arquivo `Git Branching.md` para:
- Convenções de branches
- Mensagens de commit
- Fluxo de pull requests

---

## 👥 Suporte

Para dúvidas e suporte:

- **Email**: [adicionar email de contato]
- **Issues**: https://github.com/RotaDoOeste-RoadSense/RoadSense_Infrastructure/issues

---

## 📝 Licença

[Adicionar informações de licença]

---

**Desenvolvido por**: Concessionária Nova Rota do Oeste - Equipe RDT

**Última atualização**: Novembro 2024
