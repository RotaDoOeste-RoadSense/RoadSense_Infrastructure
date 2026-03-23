# RoadSense Infrastructure - Guia Completo de Comandos

## 📋 Índice

1. [Instalação Inicial](#instalação-inicial)
2. [Gerenciamento de Serviços Docker](#gerenciamento-de-serviços-docker)
3. [Configuração do Ambiente](#configuração-do-ambiente)
4. [Processamento de Viagens](#processamento-de-viagens)
5. [Comandos do Banco de Dados](#comandos-do-banco-de-dados)
6. [Monitoramento e Debug](#monitoramento-e-debug)
7. [Manutenção do Sistema](#manutenção-do-sistema)

---

## 1️⃣ Instalação Inicial

### Pré-requisitos

```bash
# Verificar instalação do Docker
docker --version
# Saída esperada: Docker version 24.0.0 ou superior

# Verificar Docker Compose
docker compose version
# Saída esperada: Docker Compose version v2.0.0 ou superior

# Verificar drivers NVIDIA
nvidia-smi
# Deve mostrar informações da GPU

# Testar NVIDIA Docker Runtime
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi
# Deve exibir informações da GPU dentro do container
```

### Instalar Dependências (se necessário)

```bash
# Atualizar sistema
sudo apt-get update
sudo apt-get upgrade -y

# Instalar Docker (se não instalado)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Instalar NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### Clonar Repositório

```bash
# Clonar projeto
git clone https://github.com/RotaDoOeste-RoadSense/RoadSense_Infrastructure.git

# Entrar no diretório
cd RoadSense_Infrastructure

# Verificar branch
git branch
git status
```

---

## 2️⃣ Gerenciamento de Serviços Docker

### Comandos Básicos de Inicialização

```bash
# Navegar até o diretório de APIs
cd APIs

# OPÇÃO 1: Iniciar todos os serviços em modo desenvolvimento
docker compose up --build -d

# OPÇÃO 2: Usar script de inicialização (desenvolvimento + produção)
./start.sh

# OPÇÃO 3: Iniciar apenas alguns serviços
docker compose up -d rabbitmq sql fastapi_yolo fastapi_gps

# OPÇÃO 4: Build sem cache (quando houver mudanças significativas)
docker compose build --no-cache
docker compose up -d
```

### Verificar Status dos Serviços

```bash
# Listar todos os containers
docker compose ps

# Ver containers em execução (formato detalhado)
docker ps

# Ver todos os containers (incluindo parados)
docker ps -a

# Verificar uso de recursos
docker stats

# Ver apenas containers específicos
docker compose ps rabbitmq sql fastapi_yolo
```

### Parar Serviços

```bash
# Parar todos os serviços (mantém volumes)
docker compose down

# Usar script de parada
./stop.sh

# Parar serviço específico
docker compose stop fastapi_yolo

# Pausar container (sem parar)
docker compose pause fastapi_yolo

# Retomar container pausado
docker compose unpause fastapi_yolo
```

### Remover Serviços e Dados

```bash
# Parar e remover containers (mantém volumes)
docker compose down

# Remover containers E volumes (CUIDADO: perde dados!)
docker compose down -v

# Remover containers, volumes E imagens
./remove.sh
# OU
docker compose down -v --rmi all --remove-orphans

# Remover apenas imagens não utilizadas
docker image prune -a

# Remover tudo não utilizado (containers, networks, imagens, volumes)
docker system prune -a --volumes
```

### Reiniciar Serviços

```bash
# Reiniciar todos os serviços
docker compose restart

# Reiniciar serviço específico
docker compose restart fastapi_yolo

# Reiniciar com rebuild
docker compose down
docker compose up --build -d

# Reiniciar apenas serviços com GPU
docker compose restart fastapi_yolo fastapi_gps fastapi_defensa_yolo
```

### Logs e Monitoramento

```bash
# Ver logs de todos os serviços
docker compose logs

# Seguir logs em tempo real
docker compose logs -f

# Logs de serviço específico
docker compose logs fastapi_yolo

# Logs com timestamp
docker compose logs -f -t

# Últimas 100 linhas
docker compose logs --tail=100 fastapi_yolo

# Logs desde horário específico
docker compose logs --since 2024-01-01T10:00:00

# Logs entre horários
docker compose logs --since 2024-01-01T10:00:00 --until 2024-01-01T12:00:00

# Salvar logs em arquivo
docker compose logs > logs_$(date +%Y%m%d_%H%M%S).txt
```

### Executar Comandos em Containers

```bash
# Entrar no container (shell interativo)
docker exec -it <container_name> bash
# Exemplos:
docker exec -it rabbitmq bash
docker exec -it apis-sql-1 bash

# Executar comando único
docker exec <container_name> <comando>
# Exemplo:
docker exec apis-sql-1 psql -U myuser -d mydatabase -c "SELECT COUNT(*) FROM trips;"

# Executar como root
docker exec -it -u root <container_name> bash
```

### Rebuild de Serviços Específicos

```bash
# Rebuild de um serviço específico
docker compose build fastapi_yolo

# Rebuild sem cache
docker compose build --no-cache fastapi_yolo

# Rebuild e reiniciar
docker compose up -d --build fastapi_yolo

# Forçar recriação do container
docker compose up -d --force-recreate fastapi_yolo
```

---

## 3️⃣ Configuração do Ambiente

### Configurar Banco de Dados

```bash
# Editar credenciais do banco
nano APIs/SQL/Dockerfile

# Conteúdo a editar:
# ENV POSTGRES_DB=mydatabase
# ENV POSTGRES_USER=myuser
# ENV POSTGRES_PASSWORD=mypassword

# Rebuild após alteração
cd APIs
docker compose build sql
docker compose up -d sql
```

### Configurar RabbitMQ

```bash
# Editar credenciais
nano APIs/docker-compose.yml

# Localizar seção rabbitmq:
#   environment:
#     RABBITMQ_DEFAULT_USER: rdt
#     RABBITMQ_DEFAULT_PASS: 123456

# Rebuild e reiniciar
docker compose up -d --force-recreate rabbitmq
```

### Configurar Fluxo do Sistema

```bash
# Editar configurações gerais
cd Fluxo_sistema
nano config.yml

# Principais configurações:
# - database.url: URL de conexão ao banco
# - paths.root: Caminho para dados
# - URLs das APIs (inference, inference_gps, etc.)

# Editar script principal
nano main.py

# Configurar:
# - folder: caminho da viagem
# - trip_id: ID da viagem
# - trip_direction: 'N' ou 'S'
```

### Build do Container Fluxo Sistema

```bash
cd Fluxo_sistema

# Build padrão
./build.sh

# OU build manual
docker build \
  --build-arg USER_ID=$(id -u) \
  --build-arg GROUP_ID=$(id -g) \
  --build-arg USER_NAME=$(id -un) \
  -t fluxo .
```

### Executar Container Fluxo Sistema

```bash
# Usando script
./run_container.sh

# OU manualmente
docker run -it --name fluxo \
  -v /mnt:/mnt/ \
  -v $(pwd):/app \
  -v /home:/home \
  --network=host \
  --restart unless-stopped \
  fluxo

# Com nome customizado
./run_container.sh meu_fluxo
```

---

## 4️⃣ Processamento de Viagens

### Preparar Dados

```bash
# Estrutura esperada:
# /mnt/hd1/Extracoes/NOME_VIAGEM/
#   ├── Cube/
#   │   ├── image_0001_1.jpg
#   │   ├── image_0001_2.jpg
#   │   └── ...
#   ├── GPS_data.xlsx (opcional)
#   └── jsons/ (opcional)

# Verificar estrutura
ls -R /mnt/hd1/Extracoes/NOME_VIAGEM/

# Verificar permissões
ls -la /mnt/hd1/Extracoes/NOME_VIAGEM/
```

### Criar Nova Viagem

```bash
# Entrar no container fluxo
docker exec -it fluxo bash

# Método 1: Via Python interativo
python3
>>> import receber_nova_trip
>>> trip_id = receber_nova_trip.main('/mnt/hd1/Extracoes/NOME_VIAGEM', 'N')
>>> print(f"Trip ID: {trip_id}")
>>> exit()

# Método 2: Via script
python3 -c "
import receber_nova_trip
trip_id = receber_nova_trip.main('/mnt/hd1/Extracoes/NOME_VIAGEM', 'N')
print(f'Trip ID criado: {trip_id}')
"

# Método 3: Via curl (API externa)
curl -X POST "http://localhost:8013/new-trip/" \
  -F "path=/mnt/hd1/Extracoes/NOME_VIAGEM" \
  -F "way=N" \
  -F "starting_city=Cidade A" \
  -F "ending_city=Cidade B" \
  -F "production=false"
```

### Importar Dados GPS

```bash
# Dentro do container fluxo
python3
>>> from utils import run as import_gps
>>> trip_id = 1
>>> gps_file = 'trips/GPS_norte.xlsx'
>>> import_gps(trip_id, gps_file)
>>> exit()
```

### Importar Dados de JSONs

```bash
# Dentro do container fluxo
python3
>>> from utils import run_json_folder
>>> trip_id = 1
>>> json_folder = 'jsons/'
>>> # Importar tudo
>>> run_json_folder(trip_id, json_folder)
>>> # OU importar intervalo específico
>>> run_json_folder(trip_id, json_folder, 0, 1000)
>>> exit()
```

### Enviar Tarefas para Processamento

```bash
# Editar main.py com os dados da viagem
nano main.py

# Configurar:
# folder = "/mnt/hd1/Extracoes/NOME_VIAGEM"
# trip_id = 1
# trip_direction = 'N'
# 
# for queue in ['Placa','Matinho','Horizontal','DrenagemSuperficial','Defensas']:
#     # código de envio

# Executar script
python3 main.py

# Verificar tarefas enviadas
# Acessar: http://localhost:15672
# Login: rdt / 123456
# Ir em Queues
```

### Processar com Workers

```bash
# Abrir novo terminal no container
docker exec -it fluxo bash

# Iniciar workers de todas as disciplinas
python3 up_disciplines.py

# OU processar disciplina específica
python3
>>> from Placas import run as processar_placas
>>> folder = "/mnt/hd1/Extracoes/NOME_VIAGEM"
>>> trip_id = 1
>>> trip_direction = 'N'
>>> processar_placas(None, folder, trip_id, trip_direction)
>>> exit()
```

### Processar PGR (Point Grey Research)

```bash
# Editar main_pgr.py
nano main_pgr.py

# Configurar:
# pgr_folder = '/caminho/para/pgr'
# frames_output_folder = '/caminho/para/output'

# Enviar tarefa
python3 main_pgr.py

# Workers processarão automaticamente se up_disciplines.py estiver rodando
```

### Monitorar Progresso

```bash
# Via RabbitMQ Web UI
# http://localhost:15672
# Verificar:
# - Queues > Messages ready
# - Queues > Message rate
# - Connections

# Via logs do worker
docker logs fluxo -f

# Via banco de dados
docker exec -it apis-sql-1 psql -U myuser -d mydatabase
# SQL:
SELECT t.trip_id, t.way, COUNT(id.image_id) as total_images
FROM trips t
LEFT JOIN image_data id ON t.trip_id = id.trip_id
GROUP BY t.trip_id, t.way
ORDER BY t.trip_id DESC;
```

---

## 5️⃣ Comandos do Banco de Dados

### Conectar ao Banco

```bash
# Via Docker exec
docker exec -it apis-sql-1 psql -U myuser -d mydatabase

# Via psql local (se instalado)
psql -h localhost -p 5433 -U myuser -d mydatabase
# Senha: mypassword

# Via Python
python3
>>> from sqlalchemy import create_engine
>>> engine = create_engine("postgresql://myuser:mypassword@localhost:5433/mydatabase")
>>> conn = engine.connect()
>>> # executar queries
>>> conn.close()
>>> exit()
```

### Queries Úteis

```sql
-- Ver todas as viagens
SELECT * FROM trips ORDER BY trip_id DESC;

-- Total de imagens por viagem
SELECT trip_id, COUNT(*) as total_images 
FROM image_data 
GROUP BY trip_id
ORDER BY trip_id;

-- Placas detectadas por viagem
SELECT 
    t.trip_id,
    t.way,
    COUNT(DISTINCT apm.all_plates_matched_id) as total_plates,
    COUNT(pd.plate_details_id) as total_detections
FROM trips t
JOIN image_data id ON t.trip_id = id.trip_id
LEFT JOIN all_plates_matched apm ON id.image_id = apm.image_id
LEFT JOIN plate_details pd ON apm.all_plates_matched_id = pd.all_plates_matched_id
GROUP BY t.trip_id, t.way
ORDER BY t.trip_id;

-- Defensas detectadas
SELECT 
    t.trip_id,
    COUNT(gd.guardrail_details_id) as total_guardrails,
    AVG(gd.score) as avg_confidence
FROM trips t
JOIN image_data id ON t.trip_id = id.trip_id
JOIN guardrail_details gd ON id.image_id = gd.image_id
GROUP BY t.trip_id;

-- Elementos de drenagem por tipo
SELECT 
    detection_type,
    COUNT(*) as total,
    AVG(quality_value) as avg_quality
FROM drainage_details
GROUP BY detection_type;

-- Sinalização horizontal
SELECT 
    class_name,
    COUNT(*) as total,
    AVG(quality_score) as avg_quality
FROM horizontal_markings
GROUP BY class_name;

-- Últimas 10 imagens processadas
SELECT 
    id.image_id,
    id.image_name,
    id.latitude,
    id.longitude,
    t.trip_id,
    t.way
FROM image_data id
JOIN trips t ON id.trip_id = t.trip_id
ORDER BY id.image_id DESC
LIMIT 10;

-- Estatísticas completas de uma viagem
SELECT 
    t.trip_id,
    t.way,
    COUNT(DISTINCT id.image_id) as total_images,
    COUNT(DISTINCT pd.plate_details_id) as total_plates,
    COUNT(DISTINCT gd.guardrail_details_id) as total_guardrails,
    COUNT(DISTINCT dd.drainage_details_id) as total_drainage,
    COUNT(DISTINCT hm.horizontal_markings_id) as total_horizontal
FROM trips t
LEFT JOIN image_data id ON t.trip_id = id.trip_id
LEFT JOIN all_plates_matched apm ON id.image_id = apm.image_id
LEFT JOIN plate_details pd ON apm.all_plates_matched_id = pd.all_plates_matched_id
LEFT JOIN guardrail_details gd ON id.image_id = gd.image_id
LEFT JOIN drainage_details dd ON id.image_id = dd.image_id
LEFT JOIN horizontal_markings hm ON id.image_id = hm.image_id
WHERE t.trip_id = 1
GROUP BY t.trip_id, t.way;
```

### Backup e Restore

```bash
# BACKUP
# Backup completo
docker exec apis-sql-1 pg_dump -U myuser mydatabase > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup apenas schema
docker exec apis-sql-1 pg_dump -U myuser -s mydatabase > schema_backup.sql

# Backup apenas dados
docker exec apis-sql-1 pg_dump -U myuser -a mydatabase > data_backup.sql

# Backup de tabela específica
docker exec apis-sql-1 pg_dump -U myuser -t trips mydatabase > trips_backup.sql

# Backup comprimido
docker exec apis-sql-1 pg_dump -U myuser mydatabase | gzip > backup_$(date +%Y%m%d).sql.gz

# RESTORE
# Restore completo
cat backup_20240101_120000.sql | docker exec -i apis-sql-1 psql -U myuser -d mydatabase

# Restore comprimido
gunzip -c backup_20240101.sql.gz | docker exec -i apis-sql-1 psql -U myuser -d mydatabase

# Restore com drop e recreate
docker exec -i apis-sql-1 psql -U myuser -d postgres -c "DROP DATABASE IF EXISTS mydatabase;"
docker exec -i apis-sql-1 psql -U myuser -d postgres -c "CREATE DATABASE mydatabase;"
cat backup.sql | docker exec -i apis-sql-1 psql -U myuser -d mydatabase
```

### Manutenção do Banco

```sql
-- Vacuum (limpar e otimizar)
VACUUM ANALYZE;

-- Vacuum específico
VACUUM ANALYZE image_data;

-- Reindexar
REINDEX DATABASE mydatabase;

-- Ver tamanho do banco
SELECT pg_size_pretty(pg_database_size('mydatabase'));

-- Ver tamanho das tabelas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Limpar dados antigos (CUIDADO!)
DELETE FROM image_data WHERE trip_id = 1;
DELETE FROM trips WHERE trip_id = 1;
```

---

## 6️⃣ Monitoramento e Debug

### Verificar Status Geral

```bash
# Status de todos os containers
docker compose ps

# Uso de recursos
docker stats

# Uso de GPU
nvidia-smi

# Monitoramento contínuo de GPU
watch -n 1 nvidia-smi

# Processos usando GPU
nvidia-smi pmon

# Uso de disco
df -h

# Uso de disco por container
docker system df -v
```

### Debug de APIs

```bash
# Testar API de criação de viagem
curl -X POST "http://localhost:8013/new-trip/" \
  -F "path=/mnt/test" \
  -F "way=N" \
  -F "starting_city=A" \
  -F "ending_city=B"

# Testar API YOLO
curl -X POST "http://localhost:8010/analyze/" \
  -F "file=@/caminho/para/imagem.jpg" \
  -F "classes=0,1,2"

# Testar API GPS
curl -X POST "http://localhost:8011/predict/" \
  -F "lat=-15.5989" \
  -F "lon=-56.0949" \
  -F "x1=100" \
  -F "y1=150" \
  -F "x2=300" \
  -F "y2=400" \
  -F "cls=0"

# Testar API Defensas
curl -X POST "http://localhost:8700/analyze/" \
  -F "file=@/caminho/para/imagem.jpg"

# Ver resposta formatada
curl -X POST "http://localhost:8010/analyze/" \
  -F "file=@/caminho/para/imagem.jpg" | python3 -m json.tool
```

### Debug de Workers

```bash
# Ver logs do worker
docker logs fluxo -f

# Entrar no container
docker exec -it fluxo bash

# Testar módulo específico
python3
>>> from Placas import run as test
>>> # executar funções de teste
>>> exit()

# Verificar importações
python3 -c "from Placas import run; print('OK')"
python3 -c "from Defensa import run; print('OK')"

# Ver processos Python
docker exec fluxo ps aux | grep python
```

### Debug RabbitMQ

```bash
# Acessar Management UI
# http://localhost:15672
# Login: rdt / 123456

# Via CLI dentro do container
docker exec -it rabbitmq bash
rabbitmqctl list_queues
rabbitmqctl list_connections
rabbitmqctl list_channels

# Purgar fila (limpar mensagens)
docker exec rabbitmq rabbitmqctl purge_queue Placa
docker exec rabbitmq rabbitmqctl purge_queue Defensas

# Status do RabbitMQ
docker exec rabbitmq rabbitmqctl status
```

### Logs Detalhados

```bash
# Logs com timestamp
docker compose logs -f -t fastapi_yolo

# Logs em arquivo
docker compose logs > logs_completos.txt

# Logs de erros apenas
docker compose logs 2>&1 | grep -i error

# Logs de warns
docker compose logs 2>&1 | grep -i warn

# Logs de API específica
docker compose logs fastapi_yolo 2>&1 | grep -E "ERROR|WARNING"
```

### Performance Profiling

```bash
# Tempo de resposta de API
time curl -X POST "http://localhost:8010/analyze/" \
  -F "file=@imagem.jpg"

# Benchmark com ab (Apache Bench)
ab -n 100 -c 10 -p payload.json -T application/json http://localhost:8010/analyze/

# Uso de memória do container
docker stats --no-stream fastapi_yolo

# Top processos no container
docker exec fastapi_yolo top

# Uso de CPU/Memória Python
docker exec fluxo python3 -m cProfile script.py
```

---

## 7️⃣ Manutenção do Sistema

### Limpeza de Dados

```bash
# Limpar volumes Docker não utilizados
docker volume prune

# Limpar imagens não utilizadas
docker image prune -a

# Limpar tudo não utilizado
docker system prune -a --volumes

# Limpar logs antigos
sudo truncate -s 0 /var/lib/docker/containers/*/*-json.log

# Limpar cache do Docker build
docker builder prune
```

### Atualização de Código

```bash
# Pull de atualizações
git pull origin main

# Rebuild serviços afetados
cd APIs
docker compose build --no-cache <servico_modificado>
docker compose up -d --force-recreate <servico_modificado>

# Rebuild completo
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Atualização de Modelos

```bash
# Exemplo: Atualizar modelo YOLO
# 1. Copiar novo modelo
cp /caminho/modelo_novo.pt APIs/FASTAPI_YOLO_IMAGE/api_folder/weights/

# 2. Rebuild da API
cd APIs
docker compose build --no-cache fastapi_yolo

# 3. Reiniciar serviço
docker compose up -d --force-recreate fastapi_yolo

# 4. Testar
curl -X POST "http://localhost:8010/analyze/" \
  -F "file=@teste.jpg"
```

### Rotação de Logs

```bash
# Configurar logrotate para Docker
sudo nano /etc/logrotate.d/docker-containers

# Conteúdo:
# /var/lib/docker/containers/*/*.log {
#   rotate 7
#   daily
#   compress
#   missingok
#   delaycompress
#   copytruncate
# }

# Executar manualmente
sudo logrotate -f /etc/logrotate.d/docker-containers
```

### Monitoramento Automático

```bash
# Script de healthcheck
cat << 'EOF' > check_services.sh
#!/bin/bash
echo "=== Status dos Serviços ==="
docker compose ps

echo -e "\n=== RabbitMQ ==="
curl -s http://localhost:15672/api/healthchecks/node 2>&1 | grep -q "ok" && echo "OK" || echo "FAIL"

echo -e "\n=== PostgreSQL ==="
docker exec apis-sql-1 pg_isready -U myuser && echo "OK" || echo "FAIL"

echo -e "\n=== APIs ==="
for port in 8010 8011 8013 8700; do
  curl -s http://localhost:$port/docs > /dev/null && echo "Port $port: OK" || echo "Port $port: FAIL"
done

echo -e "\n=== GPU ==="
nvidia-smi > /dev/null && echo "OK" || echo "FAIL"
EOF

chmod +x check_services.sh
./check_services.sh
```

### Reinicialização Completa

```bash
# Parar tudo
cd APIs
docker compose down

# Limpar (CUIDADO: perde dados!)
docker compose down -v

# Rebuild completo
docker compose build --no-cache

# Iniciar
docker compose up -d

# Verificar
docker compose ps
docker compose logs -f
```

---

## 🆘 Comandos de Emergência

### Sistema Travado

```bash
# Matar todos os containers
docker kill $(docker ps -q)

# Parar Docker
sudo systemctl stop docker

# Limpar tudo
docker system prune -a --volumes -f

# Reiniciar Docker
sudo systemctl start docker

# Reiniciar do zero
cd APIs
./start.sh
```

### Banco de Dados Corrompido

```bash
# Parar serviço
docker compose stop sql

# Backup (se possível)
docker compose start sql
docker exec apis-sql-1 pg_dumpall -U myuser > emergency_backup.sql
docker compose stop sql

# Remover volume
docker volume rm apis_postgres-data

# Reiniciar (irá recriar schema)
docker compose up -d sql

# Restore se houver backup
cat emergency_backup.sql | docker exec -i apis-sql-1 psql -U myuser
```

### GPU Travada

```bash
# Verificar processos
nvidia-smi

# Matar processo específico
kill -9 <PID>

# Reiniciar containers com GPU
docker compose restart fastapi_yolo fastapi_gps fastapi_defensa_yolo

# Se persistir, reboot
sudo reboot
```

### RabbitMQ Travado

```bash
# Reiniciar
docker compose restart rabbitmq

# Se não resolver, recriar
docker compose stop rabbitmq
docker compose rm -f rabbitmq
docker volume rm apis_rabbitmq-data
docker compose up -d rabbitmq

# Verificar
curl http://localhost:15672
```

---

## 📝 Notas Finais

### Atalhos Úteis

```bash
# Alias para comandos comuns (adicionar ao ~/.bashrc)
alias dps='docker compose ps'
alias dlogs='docker compose logs -f'
alias dup='docker compose up -d'
alias ddown='docker compose down'
alias dstats='docker stats'
alias gpu='watch -n 1 nvidia-smi'
```

### Variáveis de Ambiente Importantes

```bash
# Para debug
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Para logs mais verbosos
export COMPOSE_HTTP_TIMEOUT=300
export DOCKER_CLIENT_TIMEOUT=300
```

### Comandos Docker Compose v2

```bash
# Docker Compose v2 usa 'docker compose' (sem hífen)
# Se ainda usa v1 (docker-compose), considere atualizar

# Verificar versão
docker compose version

# Migrar de v1 para v2
sudo apt-get remove docker-compose
sudo apt-get install docker-compose-plugin
```

---

**Última atualização**: Novembro 2024  
**Mantenha este documento atualizado conforme o projeto evolui!**
