# 📚 Documentação RoadSense Infrastructure - Índice Geral

## Visão Geral

Este repositório contém **4 documentos principais** de documentação:

### 1. 🚀 **GUIA_RAPIDO.md** (Comece aqui!)
- ⏱️ Setup em 5 minutos
- 📊 Processar primeira viagem
- 🔧 Comandos essenciais do dia a dia
- ❌ Checklist de troubleshooting

**👉 Use quando**: Você está começando ou precisa de uma referência rápida

---

### 2. 📖 **README.md** (Documentação completa)
- 🎯 Sobre o projeto e objetivos
- 🏗️ Arquitetura detalhada do sistema
- 📁 Estrutura completa do repositório
- 🔧 Instalação e configuração passo a passo
- 🔌 Todas as APIs com descrições
- 🗄️ Estrutura do banco de dados
- 🔄 Fluxo de trabalho completo
- 🐛 Troubleshooting avançado

**👉 Use quando**: Você quer entender o sistema completo ou está implementando novos recursos

---

### 3. ⌨️ **COMANDOS_COMPLETOS.md** (Referência de comandos)
- 📦 Comandos Docker e Docker Compose
- 🔧 Gerenciamento de serviços
- 🗄️ Comandos do banco de dados
- 📊 Monitoramento e debug
- 🔄 Manutenção do sistema
- 🆘 Comandos de emergência

**👉 Use quando**: Você precisa encontrar um comando específico rapidamente

---

### 4. 🔌 **REFERENCIA_APIS.md** (Catálogo de APIs)
- 📋 Lista completa de todas as APIs
- 🔌 Endpoints e parâmetros
- 📝 Exemplos de requisições e respostas
- 🧪 Scripts de teste

**👉 Use quando**: Você precisa integrar com uma API específica ou testar endpoints

---

## 🎯 Fluxo de Leitura Recomendado

### Para Iniciantes
```
1. GUIA_RAPIDO.md (começar aqui)
   ↓
2. README.md (seções básicas)
   ↓
3. COMANDOS_COMPLETOS.md (conforme necessário)
   ↓
4. REFERENCIA_APIS.md (quando precisar usar APIs)
```

### Para Desenvolvedores
```
1. README.md (completo)
   ↓
2. REFERENCIA_APIS.md (para desenvolvimento)
   ↓
3. COMANDOS_COMPLETOS.md (para operações)
   ↓
4. GUIA_RAPIDO.md (referência rápida)
```

### Para Operações/DevOps
```
1. GUIA_RAPIDO.md (setup inicial)
   ↓
2. COMANDOS_COMPLETOS.md (operação diária)
   ↓
3. README.md (troubleshooting)
   ↓
4. REFERENCIA_APIS.md (verificação de serviços)
```

---

## 📂 Estrutura dos Documentos

### GUIA_RAPIDO.md
```
├─ Setup Rápido (5 minutos)
├─ Processar Primeira Viagem
├─ Comandos Essenciais do Dia a Dia
├─ Checklist de Troubleshooting
├─ Estrutura de Arquivos Importantes
├─ Fluxo de Trabalho Típico
└─ Dicas Rápidas
```

### README.md
```
├─ Sobre o Projeto
├─ Arquitetura do Sistema
├─ Estrutura do Repositório
├─ Pré-requisitos
├─ Instalação e Configuração
├─ APIs Disponíveis
├─ Banco de Dados
├─ Fluxo de Trabalho
├─ Guia de Uso
└─ Troubleshooting
```

### COMANDOS_COMPLETOS.md
```
├─ Instalação Inicial
├─ Gerenciamento de Serviços Docker
├─ Configuração do Ambiente
├─ Processamento de Viagens
├─ Comandos do Banco de Dados
├─ Monitoramento e Debug
└─ Manutenção do Sistema
```

### REFERENCIA_APIS.md
```
├─ Gerenciamento de Viagens
├─ Detecção e Classificação de Placas
├─ Análise de Defensas
├─ Elementos de Drenagem
├─ Sinalização Horizontal
├─ Vegetação
├─ Geolocalização e GPS
├─ Qualidade e Pavimento
└─ Informações Geoespaciais
```

---

## 🔗 Links Rápidos por Tarefa

### "Quero instalar o sistema"
→ [GUIA_RAPIDO.md](GUIA_RAPIDO.md#-setup-rápido-5-minutos)  
→ [README.md](README.md#-instalação-e-configuração)

### "Quero processar uma viagem"
→ [GUIA_RAPIDO.md](GUIA_RAPIDO.md#-processar-primeira-viagem)  
→ [README.md](README.md#-fluxo-de-trabalho)  
→ [COMANDOS_COMPLETOS.md](COMANDOS_COMPLETOS.md#4%EF%B8%8F⃣-processamento-de-viagens)

### "Preciso de um comando específico"
→ [COMANDOS_COMPLETOS.md](COMANDOS_COMPLETOS.md)  
→ [GUIA_RAPIDO.md](GUIA_RAPIDO.md#-comandos-essenciais-do-dia-a-dia)

### "Como uso a API X?"
→ [REFERENCIA_APIS.md](REFERENCIA_APIS.md)

### "O serviço X não está funcionando"
→ [GUIA_RAPIDO.md](GUIA_RAPIDO.md#-checklist-de-troubleshooting)  
→ [README.md](README.md#-troubleshooting)  
→ [COMANDOS_COMPLETOS.md](COMANDOS_COMPLETOS.md#-monitoramento-e-debug)

### "Quero entender a arquitetura"
→ [README.md](README.md#️-arquitetura-do-sistema)

### "Preciso fazer backup"
→ [COMANDOS_COMPLETOS.md](COMANDOS_COMPLETOS.md#backup-e-restore)  
→ [README.md](README.md#-segurança-e-boas-práticas)

### "Como contribuir com código?"
→ [Git Branching.md](Git%20Branching.md)  
→ [README.md](README.md)

---

## 📊 Resumo do Sistema

### Componentes Principais
- **APIs**: 25+ microserviços FastAPI
- **Banco**: PostgreSQL + PostGIS
- **Broker**: RabbitMQ
- **Processamento**: Workers Python
- **IA**: Modelos de IA, TensorRT, SAM, VAE

### Portas Principais
| Serviço | Porta | Documento |
|---------|-------|-----------|
| RabbitMQ Management | 15672 | GUIA_RAPIDO.md |
| PostgreSQL | 5433 | README.md |
| Sign Detection | 8010 | REFERENCIA_APIS.md |
| GPS Predict | 8011 | REFERENCIA_APIS.md |
| New Trip | 8013 | REFERENCIA_APIS.md |
| Defensa Detection | 8700 | REFERENCIA_APIS.md |

### Comandos Mais Usados
```bash
# Iniciar sistema
cd APIs && ./start.sh

# Ver status
docker compose ps

# Ver logs
docker compose logs -f

# Processar viagem
cd Fluxo_sistema && python3 main.py

# Iniciar workers
python3 up_disciplines.py

# Parar sistema
cd APIs && ./stop.sh
```

---

## 🎓 Curva de Aprendizado

### Dia 1: Básico
- ✅ Ler GUIA_RAPIDO.md completo
- ✅ Instalar e iniciar serviços
- ✅ Processar primeira viagem de teste
- ✅ Navegar pelo RabbitMQ UI

### Semana 1: Intermediário
- ✅ Ler README.md completo
- ✅ Entender arquitetura do sistema
- ✅ Processar múltiplas viagens
- ✅ Usar queries do banco de dados
- ✅ Conhecer principais APIs

### Mês 1: Avançado
- ✅ Dominar COMANDOS_COMPLETOS.md
- ✅ Integrar com todas as APIs
- ✅ Otimizar processamento
- ✅ Realizar troubleshooting avançado
- ✅ Contribuir com melhorias

---

## 🆘 Suporte Rápido

### Problema Comum #1: Serviço não inicia
```bash
# Ver erro
docker compose logs <servico>

# Solução comum
docker compose build --no-cache <servico>
docker compose up -d --force-recreate <servico>
```
📖 Mais detalhes: [GUIA_RAPIDO.md](GUIA_RAPIDO.md#-checklist-de-troubleshooting)

### Problema Comum #2: GPU não reconhecida
```bash
# Testar
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi

# Se falhar
sudo systemctl restart docker
```
📖 Mais detalhes: [README.md](README.md#problema-container-não-inicia-com-gpu)

### Problema Comum #3: Worker não processa
```bash
# Verificar RabbitMQ
docker compose ps rabbitmq

# Reiniciar worker
# Ctrl+C no terminal do worker
python3 up_disciplines.py
```
📖 Mais detalhes: [COMANDOS_COMPLETOS.md](COMANDOS_COMPLETOS.md#debug-de-workers)

---

## 📝 Checklist de Referência Rápida

### Antes de Iniciar o Sistema
- [ ] Docker e Docker Compose instalados
- [ ] NVIDIA drivers e nvidia-docker2 instalados
- [ ] GPU testada com nvidia-smi
- [ ] Disco com espaço suficiente (>500GB)
- [ ] Dados organizados em estrutura correta

### Operação Diária
- [ ] Serviços iniciados (`./start.sh`)
- [ ] RabbitMQ acessível (http://localhost:15672)
- [ ] PostgreSQL respondendo
- [ ] Logs sendo monitorados
- [ ] GPU com memória disponível

### Processar Nova Viagem
- [ ] Dados preparados na estrutura correta
- [ ] Trip criado no banco (trip_id)
- [ ] Tarefas enviadas para RabbitMQ
- [ ] Workers em execução
- [ ] Progresso sendo monitorado

### Troubleshooting
- [ ] Verificar logs (`docker compose logs -f`)
- [ ] Verificar status (`docker compose ps`)
- [ ] Testar APIs individuais (curl)
- [ ] Verificar filas RabbitMQ
- [ ] Consultar banco de dados

---

## 🎯 Próximos Passos

Após dominar toda a documentação:

1. ✅ **Otimização**: Ajuste parâmetros de processamento
2. ✅ **Customização**: Adapte para suas necessidades
3. ✅ **Automação**: Crie scripts de automação
4. ✅ **Monitoramento**: Configure alertas
5. ✅ **Contribuição**: Proponha melhorias via Git

---

## 📚 Documentos Originais

- `README.md` - Documentação original do projeto
- `Git Branching.md` - Estratégia de branches e commits

---

## 🔄 Atualizações

- **Novembro 2024**: Documentação completa criada
  - README.md
  - COMANDOS_COMPLETOS.md
  - GUIA_RAPIDO.md
  - REFERENCIA_APIS.md
  - INDICE.md (este arquivo)

---

## 💡 Dica Final

**Imprima ou mantenha aberto**: `GUIA_RAPIDO.md` para referência diária!

**Use os atalhos**: Adicione os alias sugeridos no `GUIA_RAPIDO.md` ao seu `~/.bashrc`

**Explore os exemplos**: Todos os documentos têm exemplos práticos e testados

**Contribua**: Encontrou algo que pode melhorar? Abra uma issue ou PR!

---

**Desenvolvido por**: Equipe RoadSense - Concessionária Nova Rota do Oeste  
**Data**: Novembro 2024  
**Versão da Documentação**: 1.0

---

## 📞 Contatos e Links

- **Repositório**: https://github.com/RotaDoOeste-RoadSense/RoadSense_Infrastructure
- **Issues**: https://github.com/RotaDoOeste-RoadSense/RoadSense_Infrastructure/issues

---

**Boa sorte com o RoadSense Infrastructure! 🚀**
