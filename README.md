# V.A.D.E.R. 🦅
**Visualizador Analítico de Dados de Engenharia e Rastreio**

O **V.A.D.E.R.** é uma aplicação web local desenvolvida em Python e Streamlit, projetada para a ingestão, processamento e visualização interativa de telemetria de voo extraída de equipamentos VADR (Flight Data Recorder / Cockpit Voice Recorder), com foco inicial na aeronave A-29.

O objetivo do sistema é correlacionar comandos de voo, atitude espacial, performance do grupo motopropulsor e mensagens de falha (EICAS) em uma linha do tempo unificada, facilitando o *troubleshooting* avançado na linha de manutenção.

---

## 🛠️ Tecnologias Utilizadas
* **Linguagem:** Python 3.9+
* **Interface e Dashboard:** [Streamlit](https://streamlit.io/)
* **Manipulação de Dados:** Pandas
* **Motor Parquet:** PyArrow (ou FastParquet)
* **Visualização Gráfica:** Plotly (Plotly Express e Graph Objects)
---

## 💾 Arquitetura de Dados (CSV para Parquet)
Para garantir máxima performance (60fps) na navegação pela linha do tempo e no simulador EICAS, o V.A.D.E.R. **não** processa arquivos CSV em tempo real durante a visualização.
* **Mecanismo de Cache:** Quando um novo arquivo `.csv` é inserido no sistema, ocorre um pré-processamento rápido (stripping de headers e tipagem correta). O sistema salva uma versão binária e colunar na pasta `data/processed/` com a extensão `.parquet`.
* As leituras subsequentes e o *Time Scrubbing* (navegação temporal) são feitos exclusivamente lendo o arquivo Parquet, garantindo um carregamento praticamente instantâneo e baixo consumo de memória RAM.

## 📦 Instalação e Configuração do Ambiente

Para rodar o V.A.D.E.R. na sua máquina local, siga os passos abaixo. Recomenda-se fortemente o uso de um ambiente virtual (venv) para evitar conflitos de dependências.

### 1. Clone o repositório
```bash
git clone https://seu-repositorio-git/vader.git
cd vader

### 2. Crie e ative um ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Execute a aplicação
```bash
streamlit run app.py
```

---

## 📂 Estrutura do Projeto

vader/
│
├── data/                  # Pasta ignorada pelo Git (.gitignore)
│   ├── raw/               # Onde o inspetor coloca os arquivos .csv originais do VADR
│   └── processed/         # Onde o sistema salva as versões .parquet otimizadas automaticamente
│
├── docs/                  # Documentações Técnicas
│   ├── Dicionario_de_Dados_VADER.md
│   ├── Guia_UI_EICAS.md
│   └── orientacoes.md
│
├── src/                   # Módulos Python separados
│   ├── data_loader.py     # Lógica de ingestão (CSV -> Parquet) e limpeza com Pandas
│   ├── plots.py           # Funções geradoras dos gráficos de linha do tempo
│   └── ui_components.py   # Componentes visuais do Streamlit e mostradores do EICAS
│
├── app.py                 # Arquivo principal que monta o Dashboard
├── requirements.txt       # Dependências do projeto
├── .gitignore             # Arquivos ignorados pelo repositório (data/, venv/, __pycache__/)
└── README.md              # Este arquivo

---

## 📸 Visualização
![A-29 Side View](assets/a29_sideview.png)
*Diagrama de referência da aeronave A-29.*