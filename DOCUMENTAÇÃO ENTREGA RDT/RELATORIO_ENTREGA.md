# 📔 Manual de Operação e Entrega Técnica: RoadSense Infrastructure
**Versão**: 1.0 (Entrega RDT)  
**Público-alvo**: Engenharia Civil, Gestores de Ativos e Operadores de Campo.

---

## 1. Introdução: O que é o RoadSense?
O **RoadSense** é uma ferramenta de apoio à inspeção rodoviária baseada em Inteligência Artificial. Imagine elevar o nível da inspeção de campo, que antes era manual e subjetiva, para um processo digital, auditável e automático. 

O sistema "enxerga" a rodovia através das fotos e identifica, classifica e geolocaliza todos os ativos (placas, defensas, bueiros, etc.) de forma rápida e precisa, jogando os dados diretamente em um mapa digital.

---

## 2. Conceitos Importantes (Dicionário Simples)
Para facilitar a comunicação entre a engenharia e a TI, aqui estão os termos principais:
*   **Docker / Container**: Imagine gavetas organizadas. Cada inteligência (IA) roda dentro de sua "gaveta" (container) para não misturar arquivos e garantir que tudo funcione sempre.
*   **GPU (Placa de Vídeo)**: É o processador ultra-rápido que faz a IA "pensar". O sistema usa várias GPUs simultaneamente para processar milhares de fotos por minuto.
*   **Trip (Viagem)**: É o nome que damos à pasta de fotos de uma inspeção específica (ex: Trecho Sul - Km 10 ao 50).
*   **API**: São as "portas" de comunicação do sistema. Quando o fluxo pede uma detecção de placa, ele bate na porta da API correspondente.

---

## 3. Guia Prático - Como Operar o Sistema (Passo a Passo)

### Passo 1: Organização dos Arquivos de Imagem
Antes de tudo, as fotos da rodovia devem estar organizadas no servidor/HD o padrão:
1.  As imagens devem estar em uma pasta (ex: `PGRS_2025`).
2.  Dentro desta pasta, deve existir uma subpasta chamada `/Cube` contendo as fotos separadas por câmera (quando aplicável).

### Passo 2: Ligando o Sistema (O Motor de IA)
Para iniciar as inteligências artificiais, navegue até a pasta `APIs` no terminal e digite os comandos abaixo:
```bash
# 1. Garante que os processos antigos estão fechados
./stop.sh

# 2. Inicia todos os serviços (Sign, Guardrail, Drainage, etc.)
./start.sh
```
*Dica: Você pode verificar se tudo subiu digitando `docker ps`. Se aparecer uma lista de containers "Up", o motor está ligado.*

### Passo 3: Cadastrando uma Nova Viagem (Trip)
O sistema precisa saber qual pasta ele deve processar. Para isso, usamos o **Trip Manager**:
1.  Acesse a URL de documentação: `http://localhost:8013/docs`
2.  No comando `POST /new-trip/`, clique em "Try it out".
3.  Preencha o campo `path` com o caminho da sua pasta de fotos (ex: `/mnt/hd1/Extracoes/2026`).
4.  O sistema retornará um **`trip_id`** (um número, ex: `5`). **Guarde este número!** Ele é o RG da sua inspeção no banco de dados.

### Passo 4: Executando o Processamento Automático
Agora que o motor está ligado e a viagem cadastrada, vamos rodar o fluxo principal:
1.  Vá para a pasta `Fluxo_sistema`.
2.  Execute o script principal informando o ID da viagem e a pasta:
    ```bash
    python main.py /caminho/das/imagens 5
    ```
    *Obs: O número '5' aqui é o `trip_id` obtido no passo anterior.*

### Passo 5: Analisando os Resultados
Os dados processados (X, Y, Coordenadas GPS, Tipo de Defeito) serão gravados no banco de dados SQL. 
*   **Para ver os pontos no mapa**: Você pode usar softwares como QGIS ou o visualizador interno (Porta 8022).
*   **Para gerar relatórios Excel/CSV**: Utilize as tabelas `plate_details`, `guardrail_details` e `drainage_details` do banco de dados `mydatabase`.

---

## 4. O que o sistema detecta? (Catálogo de Ativos)

### 🚦 Sinalização Vertical (Placas)
*   **O que faz**: Identifica a presença de placas, classifica o tipo (velocidade, pare, curva, etc.) e lê o número em placas de quilometragem (OCR).
*   **Finalidade**: Gerar inventário de sinalização e verificar conformidade.

### 🚧 Defensas Metálicas e Concreto (Guardrails)
*   **O que faz**: Detecta a barreira lateral, estima a área para cálculo de pintura/manutenção e utiliza uma IA de "Qualidade" para apontar amassados ou anomalias.
*   **Finalidade**: Planejamento de reparos emergenciais.

### 💧 Drenagem Superficial
*   **O que faz**: Localiza bueiros, sarjetas e galerias.
*   **Finalidade**: Verificar limpeza e obstrução de saídas de água.

### 🌿 Vegetação (Roçada)
*   **O que faz**: Classifica a altura do mato em Baixa, Média ou Alta.
*   **Finalidade**: Criar cronogramas de roçada baseados na realidade do trecho.

---

## 5. Cuidados e Troubleshooting (FAQ)
*   **Erro de "Connection Refused"**: Verifique se você rodou o `./start.sh` e se o firewall do Linux está permitindo as portas entre 8000 e 8800.
*   **Fotos não processadas**: Verifique se o caminho da pasta no Passo 3 está escrito exatamente igual (letras maiúsculas/minúsculas importam no Linux).
*   **O sistema está lento**: Verifique o uso de GPU com o comando `nvidia-smi`. Se a memória estiver no limite, pode ser necessário aumentar o tempo de espera no processamento.

---
**Elaborado pela Equipe RDT**
*Segurança e Precisão em Infraestrutura Rodoviária.*
