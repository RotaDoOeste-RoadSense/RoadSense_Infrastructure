# 🎯 RoadSense Infrastructure - Mapa Mental da Documentação

```
                        📚 RoadSense Infrastructure
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              🚀 INÍCIO      📖 COMPLETO      ⚙️ OPERAÇÃO
                    │               │               │
            ┌───────┴───────┐      │       ┌───────┴───────┐
            │               │      │       │               │
      GUIA_RAPIDO    REFERENCIA   │   COMANDOS      INDICE
         .md           _APIS      │   _COMPLETOS     .md
                        .md       │      .md
                                  │
                          README_ATUALIZADO
                                .md


═══════════════════════════════════════════════════════════════════

                    🚀 GUIA_RAPIDO.md (START HERE!)
                    ══════════════════════════════
                    
    ⏱️  Setup Rápido           │  5 minutos para começar
    ├─ Verificar pré-requisitos │  docker, nvidia-smi
    ├─ Iniciar serviços         │  ./start.sh
    └─ Verificar status         │  docker compose ps
    
    📊 Processar Viagem        │  Passo a passo
    ├─ Preparar dados           │  Estrutura de pastas
    ├─ Criar trip               │  receber_nova_trip
    ├─ Enviar tarefas           │  main.py
    ├─ Iniciar workers          │  up_disciplines.py
    └─ Monitorar                │  RabbitMQ + logs
    
    🔧 Comandos Essenciais     │  Dia a dia
    ├─ Gerenciar serviços       │  start/stop/restart
    ├─ Consultar banco          │  psql queries
    ├─ Monitorar GPU            │  nvidia-smi
    └─ Debug APIs               │  curl + logs
    
    ❌ Troubleshooting         │  Soluções rápidas
    └─ Checklists para problemas comuns


═══════════════════════════════════════════════════════════════════

              📖 README.md (DOCUMENTAÇÃO COMPLETA)
              ═════════════════════════════════════════════════
    
    🎯 Sobre o Projeto         │  Objetivos e contexto
    ├─ RDT                      │  Desenvolvimento tecnológico
    ├─ Processamento IGG/ICP    │  Pavimentos
    └─ Monitoramento Elementos  │  Faixa de domínio
    
    🏗️ Arquitetura             │  Visão geral do sistema
    ├─ Microserviços            │  Docker containers
    ├─ RabbitMQ                 │  Message broker
    ├─ PostgreSQL + PostGIS     │  Banco geoespacial
    └─ IA/ML                    │  Detector, TensorRT, SAM, VAE
    
    📁 Estrutura               │  Organização do código
    ├─ APIs/                    │  25+ microserviços
    ├─ Fluxo_sistema/           │  Workers e processamento
    └─ SQL/                     │  Schema do banco
    
    🔧 Instalação              │  Setup completo
    ├─ Pré-requisitos           │  Hardware e software
    ├─ Configuração             │  Variáveis de ambiente
    └─ Inicialização            │  Passo a passo detalhado
    
    🔌 APIs                    │  Lista e descrição
    ├─ 25+ serviços             │  Portas e funcionalidades
    └─ Exemplos de uso          │  Requisições e respostas
    
    🗄️ Banco de Dados          │  Estrutura completa
    ├─ Tabelas principais       │  Schema SQL
    ├─ Relacionamentos          │  Foreign keys
    └─ Queries úteis            │  Exemplos práticos
    
    🔄 Fluxo de Trabalho       │  Pipeline completo
    ├─ Captura → Viagem         │  trip_id
    ├─ GPS → Tarefas            │  RabbitMQ
    ├─ Workers → APIs           │  Inferência
    └─ Banco → Visualização     │  Resultados
    
    📚 Guia de Uso             │  Cenários práticos
    ├─ Processar viagem         │  Passo a passo
    ├─ Reprocessar dados        │  Com novos modelos
    └─ Disciplinas específicas  │  Placas, Defensas, etc.
    
    🐛 Troubleshooting         │  Problemas e soluções
    ├─ GPU não reconhecida      │  nvidia-docker
    ├─ RabbitMQ travado         │  Reinicialização
    ├─ Banco corrompido         │  Backup/Restore
    └─ APIs com erro            │  Debug detalhado


═══════════════════════════════════════════════════════════════════

          ⌨️ COMANDOS_COMPLETOS.md (REFERÊNCIA DE COMANDOS)
          ═════════════════════════════════════════════════════
    
    1️⃣ Instalação Inicial     │  Pré-requisitos e setup
    ├─ Verificar instalações    │  docker, nvidia
    ├─ Instalar dependências    │  apt-get, nvidia-docker2
    └─ Clonar repositório       │  git clone
    
    2️⃣ Gerenciamento Docker    │  Containers e serviços
    ├─ Iniciar                  │  up, start.sh
    ├─ Parar                    │  down, stop.sh
    ├─ Verificar                │  ps, logs, stats
    ├─ Reiniciar                │  restart, rebuild
    └─ Remover                  │  remove.sh, prune
    
    3️⃣ Configuração            │  Ambiente e variáveis
    ├─ Banco de dados           │  POSTGRES_*
    ├─ RabbitMQ                 │  RABBITMQ_*
    ├─ Fluxo sistema            │  config.yml
    └─ Build containers         │  Dockerfile, build.sh
    
    4️⃣ Processamento Viagens   │  Pipeline completo
    ├─ Preparar dados           │  Estrutura de pastas
    ├─ Criar viagem             │  receber_nova_trip
    ├─ Importar GPS/JSON        │  utils.py
    ├─ Enviar tarefas           │  main.py, RabbitMQ
    ├─ Processar workers        │  up_disciplines.py
    └─ Monitorar progresso      │  Logs, RabbitMQ UI, SQL
    
    5️⃣ Banco de Dados          │  PostgreSQL
    ├─ Conectar                 │  psql, Python
    ├─ Queries úteis            │  SELECT, JOIN, COUNT
    ├─ Backup/Restore           │  pg_dump, restore
    └─ Manutenção               │  VACUUM, REINDEX
    
    6️⃣ Monitoramento           │  Debug e logs
    ├─ Status geral             │  docker stats, nvidia-smi
    ├─ Debug APIs               │  curl, logs
    ├─ Debug workers            │  logs, testes
    ├─ RabbitMQ CLI             │  rabbitmqctl
    └─ Performance              │  profiling, benchmark
    
    7️⃣ Manutenção              │  Sistema
    ├─ Limpeza                  │  prune, volumes
    ├─ Atualização código       │  git pull, rebuild
    ├─ Atualização modelos      │  copy, rebuild
    └─ Monitoramento auto       │  Scripts, healthcheck


═══════════════════════════════════════════════════════════════════

              🔌 REFERENCIA_APIS.md (CATÁLOGO DE APIS)
              ═════════════════════════════════════════════════
    
    1️⃣ Gerenciamento           │  Viagens e dados
    └─ NEW_TRIP (8013)          │  Criar viagem
    
    2️⃣ Placas                  │  Detecção e OCR
    ├─ Detector_IMAGE (8010)        │  Detecção Detector
    ├─ SIGN_CLASS (8016)        │  Classificação
    ├─ NUMERIC_OCR (8014)       │  OCR números
    └─ CLASSIFY_KM (8015)       │  Tipo de placa
    
    3️⃣ Defensas                │  Metal e concreto
    ├─ DEFENSA_Detector (8700)      │  Detecção
    ├─ DEFENSA_VAE (8702)       │  Qualidade VAE
    └─ SAM (8703)               │  Segmentação
    
    4️⃣ Drenagem                │  Bueiros e saídas
    ├─ DRAINAGE (8035)          │  Detecção bueiros
    └─ OUTFLOW (8421)           │  Saídas d'água
    
    5️⃣ Horizontal              │  Sinalização
    └─ HORIZONTAL (8024)        │  Faixas, zebras
    
    6️⃣ Vegetação               │  Análise
    └─ VEGETACAO_CUBE (8500)    │  Classificação
    
    7️⃣ GPS e Geo               │  Localização
    ├─ GPS_PREDICT (8011)       │  Predição GPS
    ├─ BRIDGE (8018)            │  Detecção pontes
    ├─ CANTEIRO (8017)          │  Canteiro central
    ├─ PRF (8019)               │  Postos PRF
    ├─ NS_PREDICT (8020)        │  Norte/Sul
    ├─ HIGHWAY_NUM (8021)       │  Número rodovia
    └─ KM_NEAREST (8023)        │  KM mais próximo
    
    8️⃣ Qualidade               │  Análise geral
    ├─ QUALIDADE (8330)         │  Qualidade elementos
    └─ PAVIMENTO (8310)         │  Defeitos pavimento
    
    9️⃣ Visualização            │  Mapas
    └─ PLOT_COORDS (8022)       │  Mapa interativo
    
    🔌 Infraestrutura          │  Serviços base
    ├─ RabbitMQ (5672/15672)    │  Message broker
    ├─ PostgreSQL (5433)        │  Banco dados dev
    ├─ PostgreSQL Prod (5555)   │  Banco dados prod
    └─ GEOMETRIES               │  Geometrias defensas


═══════════════════════════════════════════════════════════════════

                    📑 INDICE.md (NAVEGAÇÃO)
                    ════════════════════════
    
    📚 Visão Geral             │  4 documentos principais
    ├─ GUIA_RAPIDO.md           │  Início rápido
    ├─ README.md     │  Completo
    ├─ COMANDOS_COMPLETOS.md    │  Referência
    └─ REFERENCIA_APIS.md       │  Catálogo
    
    🎯 Fluxo de Leitura        │  Por perfil
    ├─ Iniciantes               │  Guia → README → Comandos
    ├─ Desenvolvedores          │  README → APIs → Comandos
    └─ DevOps                   │  Guia → Comandos → README
    
    📂 Estrutura               │  Conteúdo de cada doc
    
    🔗 Links por Tarefa        │  Encontre rapidamente
    ├─ Instalar sistema         │  Links diretos
    ├─ Processar viagem         │  Links diretos
    ├─ Comando específico       │  Links diretos
    └─ Troubleshooting          │  Links diretos
    
    📊 Resumo                  │  Componentes e portas
    
    🎓 Curva de Aprendizado    │  Dia 1, Semana 1, Mês 1
    
    🆘 Suporte Rápido          │  Problemas comuns


═══════════════════════════════════════════════════════════════════

                        🎯 COMO USAR ESTA DOCUMENTAÇÃO
                        ═══════════════════════════════

    Primeira vez?               │  Comece com GUIA_RAPIDO.md
    ↓                           │  
    Quer entender tudo?         │  Leia README.md
    ↓                           │  
    Precisa de um comando?      │  Consulte COMANDOS_COMPLETOS.md
    ↓                           │  
    Vai usar uma API?           │  Veja REFERENCIA_APIS.md
    ↓                           │  
    Perdido?                    │  Navegue pelo INDICE.md


═══════════════════════════════════════════════════════════════════

                            🚀 QUICK START
                            ══════════════

    1. cd APIs && ./start.sh
    2. cd ../Fluxo_sistema && ./run_container.sh
    3. python3 receber_nova_trip.main('/caminho/dados', 'N')
    4. Editar main.py com trip_id
    5. python3 main.py
    6. python3 up_disciplines.py
    7. Monitorar: http://localhost:15672


═══════════════════════════════════════════════════════════════════

                        📞 LINKS E CONTATOS
                        ═══════════════════

    🔗 GitHub:    github.com/RotaDoOeste-RoadSense/RoadSense_Infrastructure
    🐛 Issues:    github.com/RotaDoOeste-RoadSense/.../issues
    🌐 RabbitMQ:  http://localhost:15672 (rdt/123456)
    🗄️ PostgreSQL: localhost:5433 (myuser/mypassword)


═══════════════════════════════════════════════════════════════════

                        ⚡ COMANDOS RÁPIDOS
                        ═══════════════════

    # Status
    docker compose ps
    docker stats
    nvidia-smi
    
    # Logs
    docker compose logs -f
    docker compose logs -f <servico>
    
    # Gerenciamento
    cd APIs
    ./start.sh      # Iniciar
    ./stop.sh       # Parar
    ./remove.sh     # Remover tudo
    
    # Banco
    docker exec -it apis-sql-1 psql -U myuser -d mydatabase
    
    # Backup
    docker exec apis-sql-1 pg_dump -U myuser mydatabase > backup.sql


═══════════════════════════════════════════════════════════════════
```

---

## 📊 Estatísticas da Documentação

- **Total de Documentos**: 5 principais + 2 originais
- **Páginas Totais**: ~150 páginas de documentação
- **Comandos Documentados**: 200+ comandos
- **APIs Documentadas**: 25+ microserviços
- **Exemplos Práticos**: 50+ exemplos testados
- **Queries SQL**: 20+ queries úteis

---

## 🎯 Escolha Seu Caminho

```
┌─────────────────────────────────────────────────────────────┐
│  👋 SOU NOVO AQUI                                           │
│     → GUIA_RAPIDO.md                                        │
│     → Setup em 5 minutos                                    │
│     → Processar primeira viagem                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  👨‍💻 SOU DESENVOLVEDOR                                       │
│     → README.md                                  │
│     → Entender arquitetura completa                         │
│     → Integrar com APIs                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🔧 SOU DEVOPS/SYSADMIN                                     │
│     → COMANDOS_COMPLETOS.md                                 │
│     → Gerenciar serviços                                    │
│     → Monitorar e fazer troubleshooting                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🔌 VOU INTEGRAR COM APIS                                   │
│     → REFERENCIA_APIS.md                                    │
│     → Ver todos os endpoints                                │
│     → Exemplos de requisições                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🗺️ ESTOU PERDIDO                                           │
│     → INDICE.md                                             │
│     → Navegar por toda documentação                         │
│     → Links diretos para tarefas                            │
└─────────────────────────────────────────────────────────────┘
```

---

**Última atualização**: Novembro 2024  
**Mantenha este mapa à mão para navegação rápida!**
