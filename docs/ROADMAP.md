# ROADMAP — V.A.D.E.R.
**Visualizador Analítico de Dados de Engenharia e Rastreio**
Versão: 1.3 | Atualizado: 09 de Abril de 2026

---

## Visão Geral das Fases

| Fase | Nome | Prioridade | Dependência |
|------|------|------------|-------------|
| **0** | Infraestrutura e Scaffolding | Crítica | — | ✅ Concluída |
| **1** | MVP — Núcleo de Dinâmica de Voo | Crítica | Fase 0 | ✅ Concluída |
| **2** | Módulo do Grupo Motopropulsor | Alta | Fase 1 | ✅ Concluída |
| **3** | Módulo de Diagnóstico e Falhas (EICAS) | Alta | Fase 1 | ✅ Concluída |
| **4** | Polimento, Performance e Handoff | Média | Fases 2 e 3 | 🔲 Pendente |

---

## FASE 0 — Infraestrutura e Scaffolding ✅

**Objetivo:** Garantir que o ambiente de desenvolvimento esteja pronto e que toda a equipe parta da mesma base de código.
**Status:** Concluída em 09/04/2026

### Entregas

- [x] Estrutura de pastas do projeto criada (`src/`, `data/raw/`, `data/processed/`, `assets/`, `docs/`)
- [x] Arquivos skeleton gerados com assinaturas de classes e métodos:
  - `src/data_loader.py` — `DataLoader`
  - `src/plots.py` — `TimelinePlotter`, `AttitudeIndicator`, `EngineGaugePlotter`
  - `src/ui_components.py` — `EICASPanel`, `SubsystemCards`, `AttitudeBox`, `TimeController`
  - `app.py` — estrutura modular com `render_sidebar()` e `render_main()`
- [x] `requirements.txt` atualizado com versões mínimas (`streamlit`, `pandas`, `plotly`, `pyarrow`)
- [x] Criar e ativar ambiente virtual (`venv`) no ambiente de desenvolvimento
- [x] Executar `pip install -r requirements.txt` e confirmar que `streamlit run app.py` sobe sem erros
- [x] Configurar `.gitignore` para ignorar `data/`, `venv/`, `__pycache__/`

---

## FASE 1 — MVP: Núcleo de Dinâmica de Voo ✅

**Objetivo:** Aplicação funcional do início ao fim: ingestão de CSV → cache Parquet → gráfico temporal interativo + sincronização de atitude.
**Status:** Concluída em 09/04/2026
**Referência:** SCS §RF01, RF02, RF03, RF05 | Dicionário de Dados — Fase 1

### Entregas

#### 1.1 — `DataLoader` (src/data_loader.py)
- [x] `_strip_metadata_headers()`: detecta linha de cabeçalho do VADR procurando "TIME" + "Rec"
- [x] `_read_raw_csv()`: pula metadados (7 linhas) + linha de unidades via `skiprows`
- [x] `_coerce_types()`: `pd.to_numeric(errors='coerce')` + forward-fill nas colunas críticas
- [x] `_resolve_time_column()`: converte `HH:MM:SS.FFF → segundos decorridos`, cria `TIME_STR`
- [x] `convert_to_parquet()` e `load_parquet()` via PyArrow (compressão Snappy)
- [x] `_parquet_is_fresh()`: comparação de `mtime` CSV vs Parquet
- [x] `ingest()`: pipeline completo — validado com 304 linhas × 259 colunas
- [x] `get_numeric_columns()`: exclui flags de validade (`*V`) e colunas administrativas
- [x] `get_row_at_time()` e `get_fault_columns()` (48 colunas MW* detectadas)

#### 1.2 — `TimelinePlotter` (src/plots.py)
- [x] `plot()`: gráfico dark mode, zoom/pan, hover com timestamp em segundos
- [x] `add_phase_bands()`: banda marrom translúcida nas fases de solo (`WOW == 0`)

#### 1.3 — `AttitudeIndicator` (src/plots.py)
- [x] `plot(pitch, roll)`: horizonte artificial com polígono de solo rotacionado por roll, escada de pitch, símbolo da aeronave em ouro, arco de roll com ponteiro dinâmico (26 traces)

#### 1.4 — `TimeController` (src/ui_components.py)
- [x] `_init_session_state()`: inicializa `st.session_state.current_time_index = 0`
- [x] `render_slider()`: slider com label `TIME_STR` ao lado
- [x] `get_snapshot()`: `df.iloc[idx]` com clamp seguro

#### 1.5 — `AttitudeBox` (src/ui_components.py)
- [x] `render()`: horizonte (3/4) + painel de métricas (ALT, MACH, PITCH, ROLL, NZ com alerta > 4G, AOA)

#### 1.6 — `app.py`
- [x] `render_sidebar()`: upload → salva em `data/raw/` → `@st.cache_data` → dropdown de coluna Y
- [x] `render_main()`: layout wide com slider, AttitudeBox, Timeline, cards básicos de subsistemas
- [x] Cursor vermelho no gráfico sincronizado com o slider (RF05)

**Critério de Aceite da Fase 1:** ✅
> Carregar um CSV de voo do A-29, navegar pelo slider de tempo e observar o horizonte artificial se movendo em sincronia com pitch e roll.

---

## FASE 2 — Módulo do Grupo Motopropulsor ✅

**Objetivo:** Adicionar cards e gauges de performance do motor para correlação entre comandos da manete e resposta da turbina.
**Status:** Concluída em 09/04/2026
**Referência:** SCS §RF04 | Dicionário de Dados — Fase 2 | Guia UI EICAS §2

### Entregas

#### 2.1 — `EngineGaugePlotter` (src/plots.py)
- [x] `_get_color()`: lógica normal/caution/warning; OP com lógica de limite mínimo invertida
- [x] `plot_gauge()`: `go.Indicator` modo gauge com zonas de fundo coloridas, needle dinâmico e threshold line
- [x] `plot_all_engine_gauges()`: 7 figuras geradas — Q, ITT, NP, NG, FF, OT, OP (validado)
- [x] `GAUGE_SPECS`: faixas operacionais e unidades centralizadas por variável
- [x] `_MIN_LIMIT_VARS`: tratamento especial para OP (alerta abaixo do limite)

#### 2.2 — `EICASPanel.render_engine_gauges()` (src/ui_components.py)
- [x] 7 gauges renderizados em `st.columns(7)` com fundo dark `#0E1117`
- [x] `EICASPanel.render()` implementado como orquestrador (chama gauges; CAS preparado para Fase 3)

#### 2.3 — `SubsystemCards` (src/ui_components.py)
- [x] `render_engine_summary_card()`: ITT + FF + Ng com cores dinâmicas
- [x] `render_landing_gear_card()`: lógica invertida LDG (0=Abaixado/verde, 1=Recolhido/amarelo) + WOW corrigido
- [x] `render_structural_load_card()`: alerta visual (borda + texto vermelhos) se `NZ > 4.0G`
- [x] `_render_pcl_card()`: card bônus com posição da Manete (PCL) e zona operacional
- [x] `render_all()`: 4 cards em `st.columns(4)`

#### Integração em `app.py`
- [x] Box Inferior substituído por `EICASPanel.render()` + `SubsystemCards.render_all()`
- [x] Bug WOW label corrigido (`SOLO` quando `WOW == 1`)

**Critério de Aceite da Fase 2:** ✅
> Ao arrastar o slider de tempo, os gauges do motor e os cards de subsistemas atualizam instantaneamente para os valores daquele segundo.

---

## FASE 3 — Módulo de Diagnóstico e Falhas (EICAS) ✅

**Objetivo:** Transformar o painel em ferramenta de *troubleshooting*: detectar, traduzir e exibir falhas no exato instante em que ocorreram.
**Status:** Concluída em 09/04/2026
**Referência:** SCS §RF04 | Dicionário de Dados — Fase 3 | Guia UI EICAS §3

### Entregas

#### 3.1 — `TimelinePlotter.add_fault_markers()` (src/plots.py)
- [x] Varre colunas MW1_*, MW2_*, MW3_* e adiciona marcadores `x-open` no gráfico para cada flag == 1
- [x] Y-value usa a coluna plotada atualmente (parâmetro `y_column`) para sobrepor à curva
- [x] Tooltip com nome curto da falha, timestamp e valor da série
- [x] Performance corrigida: usa `df.loc[mask]` ao invés de loop `df[df["TIME"]==t]`
- [x] `legendgroup="faults"` agrupa todas as falhas na legenda

#### 3.2 — `DataLoader.get_fault_columns()` (src/data_loader.py)
- [x] Implementado (Fase 1): filtra colunas com prefixo `MW1_`, `MW2_`, `MW3_` — 48 colunas detectadas

#### 3.3 — `EICASPanel` — Janela CAS (src/ui_components.py)
- [x] `FAULT_DESCRIPTIONS`: 48 entradas mapeando colunas MW* para texto e severidade (warning/caution)
- [x] `_translate_mwc_code()`: lookup em `MWC_TRANSLATION`; fallback `"MWC CODE {n}"` para desconhecidos
- [x] `_collect_active_faults()`: retorna lista de (coluna, descrição, severidade) onde flag == 1
- [x] `render_cas_window()`:
  - Normal → painel preto com "VOO NORMAL" em cinza escuro
  - WARNINGS (vermelho, borda esquerda) sempre acima dos CAUTIONS (amarelo, borda esquerda)
  - Header mostra contagem `W / C` quando há alertas
  - Borda do painel muda de cor conforme severidade máxima

#### 3.4 — Integração em `app.py`
- [x] `add_fault_markers(fig, df, fault_columns, y_column=y_col)` conectado ao gráfico central
- [x] `EICASPanel.render(snapshot, fault_columns)` já recebia fault_columns desde a Fase 2
- [x] `render()` orquestra gauges + leitura de `MWC_DATA` + `render_cas_window()`

**Critério de Aceite da Fase 3:** ✅
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
