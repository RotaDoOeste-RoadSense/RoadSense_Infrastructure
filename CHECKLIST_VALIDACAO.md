# ✅ RoadSense Infrastructure - Checklist de Validação

## 📋 Use esta lista para verificar se tudo está funcionando corretamente

---

## 1️⃣ Pré-requisitos (Antes de Iniciar)

### Hardware
- [ ] CPU com 8+ cores
- [ ] RAM: mínimo 32GB
- [ ] Armazenamento: mínimo 500GB livres
- [ ] GPU NVIDIA (GTX 1080 Ti ou superior)

### Software Base
```bash
# Execute cada comando e marque [x] se funcionar

- [ ] docker --version
      # Deve mostrar: Docker version 24.0.0 ou superior
      
- [ ] docker compose version
      # Deve mostrar: Docker Compose version v2.0.0 ou superior
      
- [ ] nvidia-smi
      # Deve exibir informações da GPU
      
- [ ] docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi
      # Deve exibir GPU dentro do container
```

---

## 2️⃣ Instalação dos Serviços

### Clone e Estrutura
```bash
- [ ] cd RoadSense_Infrastructure
- [ ] ls -la
      # Deve listar: APIs/, Fluxo_sistema/, README.md, etc.
```

### Inicialização
```bash
- [ ] cd APIs
- [ ] ./start.sh
      # Aguardar containers subirem (pode demorar 5-10 min na primeira vez)
```

### Verificar Containers
```bash
- [ ] docker compose ps
      # Todos os serviços devem estar "running" ou "healthy"
      
      Verifique especificamente:
      - [ ] rabbitmq         (running, healthy)
      - [ ] sql              (running)
      - [ ] sign_detector     (running)
      - [ ] geo_gps_predictor (running)
      - [ ] trip_manager      (running)
      - [ ] sign_classifier   (running)
      - [ ] lightglue_tracker (running)
      - [ ] guardrail_detector (running)
      - [ ] guardrail_quality  (running)
      - [ ] guardrail_segmenter (running)
      - [ ] drainage_detector  (running)
      - [ ] outflow_detector   (running)
      - [ ] horizontal_marking_analyst (running)
      - [ ] vegetation_cube_analyst (running)
      - [ ] geometries            (exited 0 - normal)
```

---

## 3️⃣ Validação de Serviços

### RabbitMQ
```bash
- [ ] Acessar: http://localhost:15673
      Login: rdt
      Senha: 123456
      
- [ ] Dashboard carrega corretamente
- [ ] Aba "Queues" mostra filas vazias (Placa, Vegetacao, Horizontal, DrenagemSuperficial, Defensas, PGR)
- [ ] Aba "Connections" (pode estar vazia inicialmente)

- [ ] curl -u rdt:123456 http://localhost:15673/api/overview
      # Deve retornar JSON com informações do RabbitMQ
```

### PostgreSQL
```bash
- [ ] docker exec -it apis-sql-1 pg_isready -U myuser
      # Deve retornar: accepting connections
      
- [ ] docker exec -it apis-sql-1 psql -U myuser -d mydatabase -c "SELECT 1;"
      # Deve retornar: 
      #  ?column? 
      # ----------
      #         1

- [ ] docker exec -it apis-sql-1 psql -U myuser -d mydatabase -c "\dt"
      # Deve listar as tabelas: trips, image_data, plate_details, etc.
```

### APIs FastAPI
```bash
# Verificar documentação Swagger de cada API

- [ ] curl -s http://localhost:8010/docs | grep -q "Swagger"
      # Detector Image (8010)
      
- [ ] curl -s http://localhost:8011/docs | grep -q "Swagger"
      # GPS Predict (8011)
      
- [ ] curl -s http://localhost:8013/docs | grep -q "Swagger"
      # New Trip (8013)
      
- [ ] curl -s http://localhost:8016/docs | grep -q "Swagger"
      # Sign Quality Classification (8016)

- [ ] curl -s http://localhost:8714/docs | grep -q "Swagger"
      # Tracker (8714)
      
- [ ] curl -s http://localhost:8700/docs | grep -q "Swagger"
      # Defensa Detector (8700)
      
- [ ] curl -s http://localhost:8702/docs | grep -q "Swagger"
      # Defensa VAE (8702)
      
- [ ] curl -s http://localhost:8703/docs | grep -q "Swagger"
      # SAM (8703)
      
- [ ] curl -s http://localhost:8024/docs | grep -q "Swagger"
      # Horizontal (8024)
      
- [ ] curl -s http://localhost:8500/docs | grep -q "Swagger"
      # Vegetação (8500)
      
- [ ] curl -s http://localhost:8035/docs | grep -q "Swagger"
      # Drainage (8035)
      
- [ ] curl -s http://localhost:8421/docs | grep -q "Swagger"
      # Outflow (8421)
```

### GPU Disponível para Containers
```bash
- [ ] docker exec plate nvidia-smi
      # Deve exibir informações da GPU
      
- [ ] docker exec tracker nvidia-smi
      # Deve exibir informações da GPU
      
- [ ] docker exec defensa_container nvidia-smi
      # Deve exibir informações da GPU
```

---

## 4️⃣ Teste Funcional Básico

### Criar Viagem de Teste
```bash
- [ ] cd ../Fluxo_sistema
- [ ] ./run_container.sh
      # Container deve iniciar

Dentro do container:
- [ ] python3 -c "import receber_nova_trip; print('OK')"
      # Deve imprimir: OK (sem erros)
```

### Teste de API - New Trip
```bash
# Fora do container (em outro terminal)
- [ ] curl -X POST "http://localhost:8013/new-trip/" \
        -F "path=/tmp/test_trip" \
        -F "way=N" \
        -F "starting_city=Test A" \
        -F "ending_city=Test B" \
        -F "production=false"
      
      # Deve retornar algo como:
      # {"trip_id": 1, "message": "Trip created successfully"}
      
- [ ] docker exec -it apis-sql-1 psql -U myuser -d mydatabase \
        -c "SELECT * FROM trips ORDER BY trip_id DESC LIMIT 1;"
      # Deve mostrar o trip recém-criado
```

### Teste de API - Detector (com imagem de teste)
```bash
# Baixar imagem de teste
- [ ] curl -o /tmp/test_image.jpg https://via.placeholder.com/640x480.jpg

# Testar API
- [ ] curl -X POST "http://localhost:8010/analyze/" \
        -F "file=@/tmp/test_image.jpg" \
        -F "classes=0,1,2"
      
      # Deve retornar JSON (mesmo que sem detecções)
      # {"detections": [], ...} ou similar
```

### Teste de API - GPS Predict
```bash
- [ ] curl -X POST "http://localhost:8011/predict/" \
        -F "lat=-15.5989" \
        -F "lon=-56.0949" \
        -F "x1=100" \
        -F "y1=150" \
        -F "x2=300" \
        -F "y2=400" \
        -F "cls=0"
      
      # Deve retornar:
      # {"dlat": "...", "dlon": "..."}
```

---

## 5️⃣ Validação do Fluxo de Processamento

### Workers
```bash
# Dentro do container fluxo_sistema
- [ ] python3 -c "from Placas import run; print('Placas: OK')"
- [ ] python3 -c "from Defensa import run; print('Defensa: OK')"
- [ ] python3 -c "from Drenagem import run; print('Drenagem: OK')"
- [ ] python3 -c "from Horizontal import run; print('Horizontal: OK')"
- [ ] python3 -c "from Vegetacao import run; print('Vegetacao: OK')"
      # Todos devem imprimir OK
```

### RabbitMQ - Envio de Mensagem de Teste
```bash
# Dentro do container fluxo_sistema
- [ ] python3 << 'EOF'
import pika
import json

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='localhost',
        credentials=pika.PlainCredentials('rdt', '123456')
    )
)
channel = connection.channel()
channel.queue_declare(queue='test_queue', durable=True)
channel.basic_publish(
    exchange='',
    routing_key='test_queue',
    body=json.dumps({"test": "message"}),
    properties=pika.BasicProperties(delivery_mode=2)
)
print("Mensagem enviada para test_queue")
connection.close()
EOF

- [ ] Verificar no RabbitMQ UI (http://localhost:15673)
      Aba Queues → deve aparecer 'test_queue' com 1 mensagem

- [ ] Purgar fila de teste:
      docker exec rabbitmq rabbitmqctl purge_queue test_queue
```

---

## 6️⃣ Monitoramento e Logs

### Logs sem Erros Críticos
```bash
- [ ] docker compose logs | grep -i error | wc -l
      # Idealmente 0, ou apenas erros conhecidos/esperados
      
- [ ] docker compose logs rabbitmq | grep -i "started"
      # Deve mostrar "Server startup complete"
      
- [ ] docker compose logs sql | grep -i "ready"
      # Deve mostrar "database system is ready to accept connections"
```

### Uso de Recursos
```bash
- [ ] docker stats --no-stream
      # Verificar uso de CPU/Memória
      # Nenhum container deve estar usando 100% CPU constantemente
      # Uso de memória deve estar dentro dos limites esperados
      
- [ ] nvidia-smi
      # GPU não deve estar com memória esgotada
      # Deve ter espaço livre para processamento
```

---

## 7️⃣ Teste de Processamento Completo (Opcional)

### Se você tem dados de teste reais:

```bash
- [ ] Estrutura de dados correta:
      /mnt/dados/TEST_TRIP/
      └── Cube/
          ├── image_0001_1.jpg
          ├── image_0001_2.jpg
          └── ...

- [ ] Criar trip:
      python3 -c "
      import receber_nova_trip
      trip_id = receber_nova_trip.main('/mnt/dados/TEST_TRIP', 'N')
      print(f'Trip ID: {trip_id}')
      "

- [ ] Verificar trip no banco:
      docker exec -it apis-sql-1 psql -U myuser -d mydatabase \
        -c "SELECT * FROM trips WHERE trip_id = <TRIP_ID>;"

- [ ] Enviar tarefa de teste (apenas Placa):
      # Editar main.py para processar apenas 'Placa'
      # E usar o trip_id criado
      python3 main.py

- [ ] Verificar fila no RabbitMQ:
      # http://localhost:15673 → Queues → 'Placa' deve ter 1 mensagem

- [ ] Iniciar worker (em outro terminal do container):
      python3 up_disciplines.py

- [ ] Monitorar processamento:
      docker logs fluxo -f
      
- [ ] Verificar resultados no banco:
      docker exec -it apis-sql-1 psql -U myuser -d mydatabase \
        -c "SELECT COUNT(*) FROM plate_details;"
```

---

## 8️⃣ Limpeza e Reset (Para Testes)

### Se precisar resetar para estado inicial:

```bash
- [ ] Parar todos os serviços:
      cd APIs
      docker compose down

- [ ] Remover volumes (CUIDADO: apaga dados!):
      docker compose down -v

- [ ] Limpar imagens:
      docker image prune -a

- [ ] Reiniciar:
      ./start.sh
      
- [ ] Revalidar do item 2️⃣ em diante
```

---

## 9️⃣ Documentação Disponível

### Verificar arquivos de documentação:

```bash
- [ ] README.md (atualizado com links)
- [ ] GUIA_RAPIDO.md
- [ ] COMANDOS_COMPLETOS.md
- [ ] REFERENCIA_APIS.md
- [ ] INDICE.md
- [ ] MAPA_DOCUMENTACAO.md
- [ ] CHECKLIST_VALIDACAO.md (este arquivo)
- [ ] Git Branching.md
```

---

## 🎯 Resumo Final

### ✅ Sistema está OK se:

- [ ] Todos os containers estão rodando
- [ ] RabbitMQ UI acessível e funcional
- [ ] PostgreSQL aceita conexões
- [ ] APIs retornam documentação Swagger
- [ ] GPU disponível nos containers
- [ ] Teste de criação de trip funciona
- [ ] Teste de API retorna respostas válidas
- [ ] Workers podem importar módulos sem erro
- [ ] Logs não mostram erros críticos

### ❌ Se algo falhou:

1. Anote qual item falhou
2. Consulte a seção de Troubleshooting:
   - **GUIA_RAPIDO.md** - Problemas comuns
   - **README.md** - Troubleshooting detalhado
   - **COMANDOS_COMPLETOS.md** - Comandos de debug

3. Verificações comuns:
   ```bash
   # Ver logs específicos
   docker compose logs <servico_com_problema>
   
   # Reiniciar serviço específico
   docker compose restart <servico_com_problema>
   
   # Rebuild se necessário
   docker compose build --no-cache <servico_com_problema>
   docker compose up -d --force-recreate <servico_com_problema>
   ```

---

## 📊 Relatório de Validação

**Data da validação**: _______________

**Validado por**: _______________

**Resultado geral**: [ ] ✅ Aprovado  [ ] ⚠️ Com ressalvas  [ ] ❌ Reprovado

**Observações**:
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

**Itens que falharam**:
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

**Ações tomadas**:
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

---

## 🔄 Próximos Passos

Após validação completa:

1. [ ] Ler **GUIA_RAPIDO.md** para familiarização
2. [ ] Processar primeira viagem real
3. [ ] Explorar APIs na documentação **REFERENCIA_APIS.md**
4. [ ] Configurar monitoramento contínuo
5. [ ] Criar backups automáticos
6. [ ] Documentar configurações específicas do seu ambiente

---

**Última atualização**: Novembro 2024  
**Versão do checklist**: 1.0

**💡 Dica**: Salve este checklist preenchido para referência futura e auditorias!
