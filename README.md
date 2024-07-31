# README

## Sobre o Projeto

Bem-vindo ao repositório do projeto **RDT – Recurso de Desenvolvimento Tecnológico** da **Concessionária Nova Rota do Oeste**. Este projeto visa desenvolver tecnologias avançadas para identificação e avaliação automatizada de defeitos em pavimentos e elementos viários usando Inteligência Artificial (IA).

### Projetos em Desenvolvimento

#### Desenvolvimento de Tecnologia para Processamento Automático do IGG e ICP Utilizando Inteligência Artificial

- **Objetivo Geral:** Criar uma tecnologia nacional para o levantamento e processamento automático de defeitos superficiais dos pavimentos através do Levantamento Visual Contínuo Informatizado (LVCI).
- **Objetivos Específicos:**
  - Desenvolvimento do dispositivo de LVCI.
  - Desenvolvimento e treinamento da IA.
  - Avaliação e ajustes da metodologia.
  - Desenvolvimento de uma interface amigável para apresentação dos resultados.

#### Inteligência Artificial no Monitoramento dos Elementos na Faixa de Domínio

- **Objetivo Geral:** Desenvolver uma IA para identificar, georreferenciar, cadastrar e avaliar automaticamente os elementos viários na faixa de domínio.
- **Objetivos Específicos:**
  - Aquisição e montagem dos dispositivos para levantamento dos elementos viários.
  - Desenvolvimento e treinamento da IA para identificação e avaliação dos elementos viários.
  - Análise da capacidade dos algoritmos de detecção e avaliação.
  - Ajuste do processamento e comparação com dados obtidos por métodos convencionais.
  - Validação da tecnologia de IA e desenvolvimento de uma interface flexível e de fácil usabilidade.

### Arquitetura

Os projetos utilizam uma arquitetura baseada em microserviços com containers Docker. Esta abordagem é planejada para escalabilidade horizontal, mitigação de falhas e vulnerabilidades, garantindo que a aplicação possa ser adaptada a diferentes rodovias, estados e empresas com o menor acoplamento possível.

### Estrutura do Repositório

Aqui está uma breve descrição dos arquivos e pastas incluídos neste repositório:

- **`FASTAPI_CLASSIFICAR_PLACAS_KM`**: API para classificação de imagens usando um modelo de rede neural treinado.
- **`FASTAPI_GET_NEW_TRECHO`**: API para criar um novo ID de viagem e definir a estrutura do banco de dados.
- **`PREVISÃO_GPS_FASTAPI`**: API para prever coordenadas GPS com um modelo de rede neural treinado.
- **`OCR_NUMÉRICO_FASTAPI`**: API para extrair e ordenar texto de imagens usando OCR.
- **`FASTAPI_TRECHO_PREDICT`**: API para buscar o segmento de estrada mais próximo e realizar outras análises geoespaciais.
- **`IMAGEM_FASTAPI_YOLO`**: API para análise de imagens com YOLO, retornando informações sobre a detecção de objetos.
- **`FASTAPI_YOLO_IMAGE_TENSORRT`**: Serviço FastAPI para análise de imagens usando TensorRT e YOLOv8.
- **`CAMINHÃO_FASTAPI_YOLO_IMAGE`**: Pipeline de inferência para YOLOv8, otimizando a detecção de objetos na GPU.
- **`FASTAPI_YOLO_PAVIMENTO`**: API para detecção e segmentação de objetos em imagens com YOLOv8.
- **`SQL`**: Scripts para criação de tabelas no banco de dados, gerenciando dados relacionados a viagens, imagens, manutenção e mais.

### Contribuindo

Se você deseja contribuir para este projeto, siga estas etapas:

1. Fork o repositório.
2. Crie uma branch para sua nova feature (`git checkout -b feature/nova-feature`).
3. Faça commit das suas alterações (`git commit -am 'Adiciona nova feature'`).
4. Envie a branch para o repositório remoto (`git push origin feature/nova-feature`).
5. Abra um Pull Request.

### Contato

Para mais informações, dúvidas ou sugestões, entre em contato com a equipe de desenvolvimento através do e-mail [contato@exemplo.com](mailto:contato@exemplo.com).

---

Obrigado por seu interesse e colaboração! 🚀
