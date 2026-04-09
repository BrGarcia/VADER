# ROADMAP — V.A.D.E.R.
**Visualizador Analítico de Dados de Engenharia e Rastreio**
Versão: 1.0 | Data: 09 de Abril de 2026

---

## Visão Geral das Fases

| Fase | Nome | Prioridade | Dependência |
|------|------|------------|-------------|
| **0** | Infraestrutura e Scaffolding | Crítica | — |
| **1** | MVP — Núcleo de Dinâmica de Voo | Crítica | Fase 0 |
| **2** | Módulo do Grupo Motopropulsor | Alta | Fase 1 |
| **3** | Módulo de Diagnóstico e Falhas (EICAS) | Alta | Fase 1 |
| **4** | Polimento, Performance e Handoff | Média | Fases 2 e 3 |

---

## FASE 0 — Infraestrutura e Scaffolding

**Objetivo:** Garantir que o ambiente de desenvolvimento esteja pronto e que toda a equipe parta da mesma base de código.

### Entregas

- [x] Estrutura de pastas do projeto criada (`src/`, `data/raw/`, `data/processed/`, `assets/`, `docs/`)
- [x] Arquivos skeleton gerados com assinaturas de classes e métodos:
  - `src/data_loader.py` — `DataLoader`
  - `src/plots.py` — `TimelinePlotter`, `AttitudeIndicator`, `EngineGaugePlotter`
  - `src/ui_components.py` — `EICASPanel`, `SubsystemCards`, `AttitudeBox`, `TimeController`
  - `app.py` — estrutura modular com `render_sidebar()` e `render_main()`
- [x] `requirements.txt` atualizado com versões mínimas (`streamlit`, `pandas`, `plotly`, `pyarrow`)
- [ ] Criar e ativar ambiente virtual (`venv`) no ambiente de desenvolvimento
- [ ] Executar `pip install -r requirements.txt` e confirmar que `streamlit run app.py` sobe sem erros
- [ ] Configurar `.gitignore` para ignorar `data/`, `venv/`, `__pycache__/`

---

## FASE 1 — MVP: Núcleo de Dinâmica de Voo

**Objetivo:** Aplicação funcional do início ao fim: ingestão de CSV → cache Parquet → gráfico temporal interativo + sincronização de atitude.

**Referência:** SCS §RF01, RF02, RF03, RF05 | Dicionário de Dados — Fase 1

### Entregas

#### 1.1 — `DataLoader` (src/data_loader.py)
- [ ] Implementar `_strip_metadata_headers()`: detectar linha inicial dos dados no CSV do VADR
- [ ] Implementar `_read_raw_csv()`: ler CSV com `skiprows` correto via Pandas
- [ ] Implementar `_coerce_types()`: converter colunas para `float`, `int`, `datetime`; tratar `NaN` com `pd.to_numeric(errors='coerce')`
- [ ] Implementar `_resolve_time_column()`: normalizar `TIME` / `STIME` para coluna única `TIME`
- [ ] Implementar `convert_to_parquet()` e `load_parquet()` via PyArrow
- [ ] Implementar `_parquet_is_fresh()`: comparar `mtime` do CSV vs Parquet para decidir reprocessamento
- [ ] Implementar `ingest()`: pipeline completo CSV → Parquet → DataFrame
- [ ] Implementar `get_numeric_columns()` e `get_row_at_time()`

**Variáveis obrigatórias da Fase 1:** `TIME/STIME`, `BALT`, `MACH`, `AOA`, `APA`, `ARA`, `NZ`, `WOW`, `LDG`

#### 1.2 — `TimelinePlotter` (src/plots.py)
- [ ] Implementar `plot()`: gráfico Plotly com Eixo X = TIME, Eixo Y = coluna selecionada; zoom/pan habilitados
- [ ] Implementar `add_phase_bands()`: sombrear fases de voo usando `WOW`

#### 1.3 — `AttitudeIndicator` (src/plots.py)
- [ ] Implementar `plot(pitch, roll)`: horizonte artificial minimalista usando formas Plotly ou SVG

#### 1.4 — `TimeController` (src/ui_components.py)
- [ ] Implementar `_init_session_state()`: inicializar `st.session_state.current_time_index = 0`
- [ ] Implementar `render_slider()`: `st.slider` vinculado ao `session_state`
- [ ] Implementar `get_snapshot()`: retornar `df.iloc[time_index]`

#### 1.5 — `AttitudeBox` (src/ui_components.py)
- [ ] Implementar `render()`: exibir horizonte artificial + `BALT` + `MACH` em destaque numérico

#### 1.6 — `app.py`
- [ ] Implementar `render_sidebar()`: `st.file_uploader` + chamada ao `DataLoader.ingest()` + Dropdown de coluna Y
- [ ] Implementar `render_main()`: layout wide com três linhas (AttitudeBox / Timeline / Subsystems)
- [ ] Conectar o slider ao gráfico de linha do tempo (sincronização RF05)

**Critério de Aceite da Fase 1:**
> Carregar um CSV de voo do A-29, navegar pelo slider de tempo e observar o horizonte artificial se movendo em sincronia com pitch e roll.

---

## FASE 2 — Módulo do Grupo Motopropulsor

**Objetivo:** Adicionar cards e gauges de performance do motor para correlação entre comandos da manete e resposta da turbina.

**Referência:** SCS §RF04 | Dicionário de Dados — Fase 2 | Guia UI EICAS §2

### Entregas

#### 2.1 — `EngineGaugePlotter` (src/plots.py)
- [ ] Implementar `_get_color()`: lógica de cores com base em `ENGINE_LIMITS` (normal / caution / warning)
- [ ] Implementar `plot_gauge()`: `go.Indicator` no modo `gauge` com thresholds dinâmicos de cor
- [ ] Implementar `plot_all_engine_gauges()`: retornar lista de 7 figuras para `Q`, `ITT`, `NP`, `NG`, `FF`, `OT`, `OP`

**Limites de Cores:**
- Normal: `#FFFFFF` | Caution: `#FFC107` | Warning: `#FF4B4B`
- ITT Warning obrigatório acima do limite operacional (ver `ENGINE_LIMITS`)

#### 2.2 — `EICASPanel.render_engine_gauges()` (src/ui_components.py)
- [ ] Implementar renderização dos 7 gauges em colunas `st.columns(7)`
- [ ] Fundo obrigatoriamente dark (`#0E1117`) — usar `st.markdown` com CSS inline

#### 2.3 — `SubsystemCards` (src/ui_components.py)
- [ ] Implementar `render_engine_summary_card()`: ITT + FF + status resumido
- [ ] Implementar `render_landing_gear_card()`: respeitar lógica invertida `LDG` (0=Abaixado, 1=Recolhido)
- [ ] Implementar `render_structural_load_card()`: alerta visual se `NZ > 4.0G`
- [ ] Implementar `render_all()`: orquestrar os três cards em `st.columns`

**Critério de Aceite da Fase 2:**
> Ao arrastar o slider de tempo, os gauges do motor e os cards de subsistemas atualizam instantaneamente para os valores daquele segundo.

---

## FASE 3 — Módulo de Diagnóstico e Falhas (EICAS)

**Objetivo:** Transformar o painel em ferramenta de *troubleshooting*: detectar, traduzir e exibir falhas no exato instante em que ocorreram.

**Referência:** SCS §RF04 | Dicionário de Dados — Fase 3 | Guia UI EICAS §3

### Entregas

#### 3.1 — `TimelinePlotter.add_fault_markers()` (src/plots.py)
- [ ] Varrer colunas `MW1_*`, `MW2_*`, `MW3_*` no DataFrame
- [ ] Adicionar `go.Scatter` com `mode='markers'` no gráfico principal nos timestamps de falha
- [ ] Tooltip do marcador deve exibir o nome da coluna (ex: `MW1_FT1 — Perda sensor T1`)

#### 3.2 — `DataLoader.get_fault_columns()` (src/data_loader.py)
- [ ] Implementar filtragem de colunas com prefixo `MW1_`, `MW2_`, `MW3_`

#### 3.3 — `EICASPanel` — Janela CAS (src/ui_components.py)
- [ ] Implementar `_translate_mwc_code()`: mapear `MWC_TRANSLATION` dict com fallback para desconhecidos
- [ ] Implementar `_collect_active_faults()`: varrer snapshot para flags MW* == 1
- [ ] Implementar `render_cas_window()`:
  - Sem alertas → painel preto/vazio (simulação de voo normal)
  - WARNINGS (vermelho) sempre acima dos CAUTIONS (amarelo)
  - Usar `st.markdown` com HTML para colorização condicional

#### 3.4 — Integração em `app.py`
- [ ] Conectar `EICASPanel.render()` ao snapshot do `TimeController`
- [ ] Passar `fault_columns` do `DataLoader.get_fault_columns()` para o painel

**Critério de Aceite da Fase 3:**
> Ao navegar pelo timeline e passar por um segundo onde `MWC_DATA == 47`, a janela CAS exibe `ENG FIRE` em vermelho. Ao retornar a um segundo normal, o painel fica em branco.

---

## FASE 4 — Polimento, Performance e Handoff

**Objetivo:** Garantir os Requisitos Não-Funcionais (RNF) e preparar o projeto para uso em linha de manutenção.

**Referência:** SCS §RNF01, RNF02, RNF03

### Entregas

#### 4.1 — Performance
- [ ] Validar RNF01: renderização inicial < 5 segundos para 100.000 linhas
- [ ] Validar RNF02: latência de scrubbing < 100ms (perfilamento com `st.cache_data`)
- [ ] Aplicar `@st.cache_data` nas funções de leitura do `DataLoader`
- [ ] Usar `df.loc` com index otimizado para `get_row_at_time()` (evitar `iterrows`)

#### 4.2 — UX / Acessibilidade
- [ ] Garantir wide layout 100% com `st.set_page_config(layout="wide")`
- [ ] Tipografia monoespaçada nos displays numéricos do EICAS (RF UI02)
- [ ] Cards do Box Inferior quebram linha automaticamente em janelas menores (RF UI03)
- [ ] Dropdown de seleção de variável ordenado alfabeticamente

#### 4.3 — Qualidade de Código (RNF03)
- [ ] Cada card do Box Inferior é um método independente (`render_landing_gear_card`, etc.) — facilita adição futura sem refatoração do layout base
- [ ] Constantes de limites operacionais centralizadas em `ENGINE_LIMITS` e `NZ_ALERT_THRESHOLD`
- [ ] Rever e remover imports não utilizados

#### 4.4 — Documentação Final
- [ ] Atualizar `README.md` com instrução de execução e screenshot do dashboard completo
- [ ] Verificar se `.gitignore` cobre `data/`, `venv/`, `__pycache__/`, `*.parquet`

---

## Mapa de Dependências entre Módulos

```
app.py
 ├── DataLoader          (src/data_loader.py)
 │     └── PyArrow / Pandas
 ├── TimeController      (src/ui_components.py)
 ├── AttitudeBox         (src/ui_components.py)
 │     └── AttitudeIndicator  (src/plots.py)
 ├── TimelinePlotter     (src/plots.py)
 └── EICASPanel          (src/ui_components.py)
       ├── EngineGaugePlotter  (src/plots.py)
       └── SubsystemCards      (src/ui_components.py)
```

---

## Arquivos de Referência para a Equipe

| Documento | Conteúdo |
|-----------|----------|
| `SCS.md` | Especificação completa de requisitos (RF, UI, RNF) |
| `Dicionario_de_Dados_VADER.md` | Mapeamento de variáveis CSV por fase, ranges e lógica de tratamento |
| `Guia_UI_EICAS.md` | Diretrizes de UX, cores, thresholds e comportamento do painel EICAS |
| `CONTRIBUTING.md` | Padrões de contribuição e workflow de desenvolvimento |
