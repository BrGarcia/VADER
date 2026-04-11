# V.A.D.E.R. 🦅
**Visualizador Analítico de Dados de Engenharia e Rastreio**

Aplicação web local em Python/Streamlit para ingestão, processamento e visualização interativa de telemetria de voo extraída de equipamentos VADR (Flight Data Recorder), com foco na aeronave **A-29 Super Tucano**.

Correlaciona comandos de voo, atitude espacial, performance do grupo motopropulsor e mensagens de falha (EICAS) em uma linha do tempo unificada, facilitando o *troubleshooting* na linha de manutenção.

---

## Execução Rápida

```bash
# 1. Clone e entre na pasta
git clone <url-do-repositorio>
cd vader

# 2. Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Inicie a aplicação
streamlit run app.py
```

Acesse `http://localhost:8501` no navegador. Configure o arquivo no menu superior horizontal.

---

## Funcionalidades Principais

| Módulo | Descrição |
|--------|-----------|
| **Ingestão CSV → Parquet** | Detecta e pula os metadados do VADR; converte para Parquet (Snappy) para performance; reprocessa apenas se o arquivo for alterado. |
| **Linha do Tempo** | Gráfico interativo (zoom/pan) de qualquer variável numérica; bandas coloridas de voo (azul) e solo (marrom); marcadores de falha MW* integrados. |
| **Painel de Alertas** | Exibição em tempo real de falhas críticas (ENG FIRE, OIL PRESS, etc.) com efeito *ghosting* para sistemas inativos e destaque total para alertas ativos. |
| **Horizonte Artificial** | Instrumento de atitude dinâmico com pitch, roll, escada de referência e ponteiro de bank (alternável com o Painel de Alertas). |
| **Gauges do Motor (EICAS)** | 7 instrumentos técnicos: Torque, ITT, Np, Ng, Fuel Flow, Oil Temp, Oil Press — com zonas de cor e needle dinâmico. |
| **Cards de Subsistemas** | Monitoramento rápido de Trem de Pouso, Carga Estrutural (G-load), Resumo do Motor e Posição da Manete (PCL). |
| **Playback & Scrubbing** | Controle de Play/Pause (20 FPS) e slider temporal para sincronização instantânea de todos os instrumentos. |

---

## Estrutura do Projeto

```
vader/
├── app.py                  # Ponto de entrada — layout centralizado e landing page
├── requirements.txt        # Dependências do projeto
├── .gitignore
│
├── src/
│   ├── data_loader.py      # Pipeline de processamento de dados (Pandas/PyArrow)
│   ├── plots.py            # Motores gráficos Plotly (Timeline, Horizon, Gauges)
│   └── ui_components/      # Pacote de componentes Streamlit
│       ├── __init__.py     # AttitudeBox, TimeController, EICAS
│       └── fault_panel.py  # Grid dinâmico de alertas
│
├── data/                   # Diretório de dados (raw e processed)
├── assets/                 # Imagens e perfis técnicos da aeronave
└── docs/                   # Documentação técnica detalhada
```

---

## Documentação Técnica

| Documento | Conteúdo |
|-----------|----------|
| `docs/SCS.md` | Especificação completa de requisitos (RF, UI, RNF) |
| `docs/Dicionario_de_Dados_VADER.md` | Mapeamento de variáveis, ranges e lógica de tratamento |
| `docs/ROADMAP.md` | Histórico de desenvolvimento e metas futuras |
| `10ABR.MD` | Resumo detalhado das implementações de hoje |

---

![A-29 Side View](assets/a29_sideview.png)
*A-29 Super Tucano — aeronave de referência do projeto.*
