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

### Passo 3: Extraindo Imagens dos Arquivos `.pgr`
Antes de criar a trip, é necessário extrair as imagens dos arquivos `.pgr`.
1.  Entre na pasta `Fluxo_sistema` e execute o container:
    ```bash
    sh build.sh
    ```
2.  **Dentro do container**, no arquivo `main_pgr.py`, ajuste:
    - `pgr_folder` com a pasta onde estão os arquivos `.pgr`
3.  **Dentro do container**, execute:
    ```bash
    python main_pgr.py
    ```
4.  O fluxo de PGR salva as imagens em uma pasta `Cube` (padrão: dentro de `pgr_folder`).
5.  **Dentro do container**, execute:
    ```bash
    python up_disciplines.py
    ```

### Passo 4: Configurando e Executando o Fluxo Principal
Depois que a pasta `Cube` for gerada, rode o fluxo principal:
1.  Entre na pasta `Fluxo_sistema` e execute o container:
    ```bash
    sh build.sh
    ```
2.  **Dentro do container**, no arquivo `main.py`, ajuste:
    - `folder` com a **pasta que contém a pasta `Cube`**
    - `trip_direction` com `N` ou `S`
3.  **Dentro do container**, execute o script principal:
    ```bash
    python main.py
    ```
    *Obs: O `trip_id` é criado automaticamente e exibido no terminal.*
4.  **Dentro do container**, execute:
    ```bash
    python up_disciplines.py
    ```

### Passo 5: Analisando os Resultados
Os dados processados (X, Y, Coordenadas GPS, Tipo de Defeito) serão gravados no banco de dados SQL. 
*   **Para ver os pontos no mapa**: Você pode usar softwares como QGIS ou o visualizador interno disponível no seu ambiente.
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

### 🛣️ Sinalização Horizontal
*   **O que faz**: Identifica as classes `Continua`, `Segmentada`, `Legenda` e `Zebrado`.
*   **Qualidade**: Também classifica a qualidade da sinalização como `boa` ou `ruim`.
*   **Finalidade**: Apoiar manutenção de pintura e segurança viária.

---

## 5. Cuidados e Troubleshooting (FAQ)
*   **Erro de "Connection Refused"**: Verifique se você rodou o `./start.sh` e se o firewall do Linux está liberando as portas realmente usadas no ambiente (ex.: 8010, 8011, 8013, 8016, 8024, 8035, 8421, 8500, 8700, 8702, 8703, 8714, 15673, 5673, 1111 e 6381).
*   **Fotos não processadas**: Verifique se o caminho da pasta nos Passos 3 e 4 está escrito exatamente igual (letras maiúsculas/minúsculas importam no Linux).
*   **O sistema está lento**: Verifique o uso de GPU com o comando `nvidia-smi`. Se a memória estiver no limite, pode ser necessário aumentar o tempo de espera no processamento.

---
**Elaborado pela Equipe RDT**
*Segurança e Precisão em Infraestrutura Rodoviária.*
