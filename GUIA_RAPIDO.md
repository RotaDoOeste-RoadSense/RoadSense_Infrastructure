# RoadSense Infrastructure - Guia Rápido de Início

## 🚀 Setup Rápido (5 minutos)

### 1. Pré-requisitos
```bash
# Verificar instalações necessárias
docker --version && docker compose version && nvidia-smi
```

### 2. Iniciar Serviços
```bash
cd APIs
./start.sh
```

### 3. Verificar Status
```bash
docker compose ps
# Aguarde todos os serviços ficarem "healthy" ou "running"
```

### 4. Acessos Web
- **RabbitMQ**: http://localhost:15673 (rdt / 123456)
- **PostgreSQL**: localhost:1111 (myuser / mypassword)

---

## 📊 Processar Primeira Viagem

### Passo 1: Preparar Dados
```bash
# Sua estrutura de dados deve estar em:
# /mnt/hd1/Extracoes/NOME_VIAGEM/Cube/
```

### Passo 2: Criar Viagem
```bash
# Entrar no container de processamento
cd Fluxo_sistema
./run_container.sh

# Dentro do container, criar trip
python3 -c "
import receber_nova_trip
trip_id = receber_nova_trip.main('/mnt/hd1/Extracoes/NOME_VIAGEM', 'N')
print(f'Trip ID: {trip_id}')
"
# Anotar o trip_id retornado
```

### Passo 3: Enviar para Processamento
```bash
# Editar main.py com seu trip_id
nano main.py
# Alterar:
# folder = "/mnt/hd1/Extracoes/NOME_VIAGEM"
# trip_id = <seu_trip_id>
# trip_direction = 'N'  # ou 'S'

# Executar
python3 main.py
```

### Passo 4: Iniciar Workers
```bash
# Em outro terminal do container (docker exec -it fluxo bash)
python3 up_disciplines.py
```

### Passo 5: Monitorar
```bash
# RabbitMQ: http://localhost:15673
# Logs: docker logs fluxo -f
```

---

## 🔧 Comandos Essenciais do Dia a Dia

### Gerenciar Serviços
```bash
cd APIs

# Iniciar
./start.sh

# Parar
docker compose -f docker-compose.yml down

# Reiniciar serviço específico
docker compose restart sign_detector

# Ver logs
docker compose logs -f sign_detector
```

### Consultar Banco de Dados
```bash
# Conectar
docker exec -it apis-sql-1 psql -U myuser -d mydatabase

# Queries úteis:
SELECT * FROM trips ORDER BY trip_id DESC LIMIT 5;
SELECT trip_id, COUNT(*) FROM image_data GROUP BY trip_id;
```

### Monitorar GPU
```bash
# Status atual
nvidia-smi

# Monitoramento contínuo
watch -n 1 nvidia-smi
```

### Debug de APIs
```bash
# Testar API
curl -X POST "http://localhost:8010/analyze/" \
  -F "file=@teste.jpg" \
  -F "classes=0,1,2"

# Ver logs
docker compose logs -f sign_detector
```

---

## 📋 Checklist de Troubleshooting

### ❌ Serviço não inicia
```bash
# Ver erro
docker compose logs <servico>

# Rebuild
docker compose build --no-cache <servico>
docker compose up -d --force-recreate <servico>
```

### ❌ GPU não reconhecida
```bash
# Testar NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi

# Se falhar, reinstalar
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### ❌ RabbitMQ não conecta
```bash
# Verificar status
docker compose ps rabbitmq

# Reiniciar
docker compose restart rabbitmq

# Aguardar healthcheck
docker compose ps
```

### ❌ Banco de dados erro de conexão
```bash
# Verificar container
docker compose ps sql

# Testar conexão
docker exec apis-sql-1 pg_isready -U myuser

# Ver logs
docker compose logs sql
```

### ❌ Out of Memory (GPU)
```bash
# Verificar uso
nvidia-smi

# Reiniciar serviços GPU
docker compose restart sign_detector geo_gps_predictor guardrail_detector
```

---

## 📖 Estrutura de Arquivos Importantes

```
RoadSense_Infrastructure/
├── APIs/
│   ├── docker-compose.yml        # Configuração dev
│   ├── start.sh                  # Iniciar serviços
│   ├── stop.sh                   # Parar serviços
│   └── FASTAPI_*/                # Microserviços
│
├── Fluxo_sistema/
│   ├── config.yml                # Configurações gerais
│   ├── main.py                   # Enviar tarefas
│   ├── up_disciplines.py         # Workers
│   ├── build.sh                  # Build container
│   └── run_container.sh          # Executar container
│
├── README.md                     # Documentação completa
├── COMANDOS_COMPLETOS.md         # Todos os comandos
└── GUIA_RAPIDO.md               # Este arquivo
```

---

## 🎯 Fluxo de Trabalho Típico

```
1. Iniciar Serviços
   └─> cd APIs && ./start.sh

2. Preparar Container Fluxo
   └─> cd Fluxo_sistema && ./run_container.sh

3. Criar Viagem
   └─> python3 receber_nova_trip.py

4. Enviar Tarefas
   └─> Editar main.py e executar

5. Processar
   └─> python3 up_disciplines.py

6. Monitorar
   └─> http://localhost:15673 e logs

7. Consultar Resultados
   └─> Queries no PostgreSQL
```

---

## 🔗 Links Rápidos

### Documentação
- **Documentação Completa**: `README.md`
- **Todos os Comandos**: `COMANDOS_COMPLETOS.md`
- **Git Branching**: `Git Branching.md`

### Interfaces Web
- **RabbitMQ Management**: http://localhost:15673
- **API Docs (exemplo)**: http://localhost:8010/docs

### Portas Principais
| Serviço | Porta |
|---------|-------|
| RabbitMQ | 5673, 15673 |
| PostgreSQL | 1111 |
| Sign Detection | 8010 |
| GPS Predict | 8011 |
| New Trip | 8013 |
| Defensa Detection | 8700 |
| Defensa VAE | 8702 |
| Tracker | 8714 |

---

## 💡 Dicas Rápidas

### Alias Úteis (adicionar ao ~/.bashrc)
```bash
alias dps='docker compose ps'
alias dlogs='docker compose logs -f'
alias dup='docker compose up -d'
alias ddown='docker compose down'
alias gpu='watch -n 1 nvidia-smi'
```

### Ver Status Geral
```bash
# Status containers
docker compose ps

# Uso de recursos
docker stats

# GPU
nvidia-smi

# Filas RabbitMQ
curl -u rdt:123456 http://localhost:15673/api/queues | python3 -m json.tool
```

### Backup Rápido
```bash
# Banco de dados
docker exec apis-sql-1 pg_dump -U myuser mydatabase > backup_$(date +%Y%m%d).sql

# Código
git add . && git commit -m "backup" && git push
```

---

## 🆘 Suporte

### Ordem de Debug
1. **Ver logs**: `docker compose logs -f <servico>`
2. **Verificar status**: `docker compose ps`
3. **Testar API**: `curl http://localhost:<porta>/docs`
4. **Consultar banco**: `docker exec -it apis-sql-1 psql -U myuser -d mydatabase`
5. **Verificar GPU**: `nvidia-smi`
6. **Reiniciar**: `docker compose restart <servico>`

### Comandos de Emergência
```bash
# Parar tudo
docker compose down

# Limpar volumes (CUIDADO!)
docker compose down -v

# Rebuild completo
docker compose build --no-cache
docker compose up -d

# Reiniciar Docker
sudo systemctl restart docker
```

---

## 📚 Próximos Passos

Após dominar este guia rápido:

1. ✅ Leia `README.md` para entender a arquitetura completa
2. ✅ Consulte `COMANDOS_COMPLETOS.md` para comandos avançados
3. ✅ Revise `Git Branching.md` para contribuir com código
4. ✅ Experimente diferentes disciplinas (Placas, Defensas, etc.)
5. ✅ Otimize seu fluxo de trabalho com scripts customizados

---

**Última atualização**: Novembro 2024

**Dica**: Mantenha este arquivo aberto durante seu trabalho para referência rápida!
