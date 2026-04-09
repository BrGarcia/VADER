# V.A.D.E.R. 🦅
**Visualizador Analítico de Dados de Engenharia e Rastreio**

O **V.A.D.E.R.** é uma aplicação web local desenvolvida em Python e Streamlit, projetada para a ingestão, processamento e visualização interativa de telemetria de voo extraída de equipamentos VADR (Flight Data Recorder / Cockpit Voice Recorder), com foco inicial na aeronave A-29.

O objetivo do sistema é correlacionar comandos de voo, atitude espacial, performance do grupo motopropulsor e mensagens de falha (EICAS) em uma linha do tempo unificada, facilitando o *troubleshooting* avançado na linha de manutenção.

---

## 🛠️ Tecnologias Utilizadas
* **Linguagem:** Python 3.9+
* **Interface e Dashboard:** [Streamlit](https://streamlit.io/)
* **Manipulação de Dados:** Pandas
* **Visualização Gráfica:** Plotly (Plotly Express e Graph Objects)

---

## 📦 Instalação e Configuração do Ambiente

Para rodar o V.A.D.E.R. na sua máquina local, siga os passos abaixo. Recomenda-se fortemente o uso de um ambiente virtual (venv) para evitar conflitos de dependências.

### 1. Clone o repositório
```bash
git clone https://seu-repositorio-git/vader.git
cd vader
```

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
- `assets/`: Imagens e recursos visuais da aeronave A-29.
- `docs/`: Documentação detalhada, guias de UI e manuais técnicos.
- `app.py`: Ponto de entrada da aplicação Streamlit (em desenvolvimento).
- `requirements.txt`: Lista de dependências do projeto.

---

## 📸 Visualização
![A-29 Side View](assets/a29_sideview.png)
*Diagrama de referência da aeronave A-29.*