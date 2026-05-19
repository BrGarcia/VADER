# 📐 Plano de Correção — Fluidez do Gráfico "Análise Temporal"

**Data:** 2026-05-19  
**Arquivo de referência:** `src/ui/views/vadr.py`, `src/ui/plots.py`, `src/ui/components/__init__.py`  
**Sintoma:** Ao mover o slider de tempo, a aplicação demora visivelmente para atualizar, pois reconstrói o gráfico Plotly completo + todos os painéis a cada interação.

---

## Diagnóstico da Causa-Raiz

### Fluxo atual (problemático)

```
Usuário move o slider
        ↓
st.rerun() é acionado  ← linha 160 do TimeController
        ↓
render_main() é chamado inteiro novamente
        ↓
_PLOTTER.plot()         ← reconstrói todas as traces com 100k+ pontos
_PLOTTER.add_phase_bands() ← itera grupos de fases
_PLOTTER.add_fault_markers() ← itera colunas MW*
fig.add_vline()         ← adiciona cursor DENTRO do fig completo
        ↓
st.plotly_chart()       ← serializa o fig inteiro para o browser (JSON pesado)
        ↓
AttitudeBox.render()    ← recalcula horizonte artificial
SubsystemCards.render_all() ← recalcula 4 cards
FlightMap.render()      ← renderiza mapa pydeck
```

**Problema central:** O `fig` (gráfico completo com todas as traces, phase bands e fault markers) é **recriado do zero** a cada movimento de slider. Para um CSV de 10 MB com 8 Hz × 90 min ≈ 43.200 linhas × N colunas, isso é O(N×K) por rerun.

### Problemas identificados

| # | Local | Problema | Impacto |
|---|-------|---------|---------|
| P-01 | `TimeController.render_slider()` L.158-160 | `st.rerun()` no onChange do slider força full-rerun da página | 🔴 Alto |
| P-02 | `vadr.py` L.124-126 | `plot()`, `add_phase_bands()`, `add_fault_markers()` chamados sem cache | 🔴 Alto |
| P-03 | `plots.py` L.164 | Dados brutos completos (100k+ pts) enviados ao Plotly sem decimação | 🔴 Alto |
| P-04 | `vadr.py` L.130-135 | `add_vline()` força re-serialização completa do fig a cada tick | 🟠 Médio |
| P-05 | `vadr.py` L.124 | `key=f"main_plot_{y_col}"` muda ao trocar variável, recriando widget | 🟡 Baixo |
| P-06 | `vadr.py` L.142 | `st.plotly_chart()` serializa o fig inteiro como JSON a cada rerun | 🟠 Médio |

---

## Plano de Correção

### Fase A — Cache do Gráfico Base (maior ganho, menor risco)

#### A.1 — Cachear o `fig` base com `@st.cache_data`

**Arquivo:** `src/ui/plots.py` + `src/ui/views/vadr.py`

O gráfico base (traces + phase bands + fault markers) **não muda** enquanto o arquivo e as variáveis selecionadas forem os mesmos. Apenas a `vline` do cursor muda.

```python
# plots.py — nova função de módulo cacheável
@st.cache_data(show_spinner=False)
def build_base_figure(
    df: pd.DataFrame,
    y_cols: tuple[str, ...],  # tuple (hashável), não list
    fault_columns: tuple[str, ...],
) -> go.Figure:
    """Constrói o fig base (sem cursor) — cacheado por df identity + variáveis."""
    plotter = TimelinePlotter()
    fig = plotter.plot(df, list(y_cols))
    fig = plotter.add_phase_bands(fig, df)
    fig = plotter.add_fault_markers(fig, df, list(fault_columns), y_column=list(y_cols))
    return fig
```

```python
# vadr.py — uso
import copy

base_fig = build_base_figure(df, tuple(y_cols), tuple(fault_columns))
fig = copy.deepcopy(base_fig)           # cópia rasa para adicionar cursor
fig.add_vline(x=t_cursor, ...)          # cursor não polui o cache
```

**Ganho estimado:** ~80% de redução no tempo de rebuild ao mover o slider.

> [!WARNING]
> `@st.cache_data` serializa o DataFrame para hash — DataFrames grandes (>50 MB) podem ter latência de hashing. Avaliar uso de `hash_funcs` customizado ou parâmetro `ttl`.

---

#### A.2 — Decimação de pontos (down-sampling)

**Arquivo:** `src/ui/plots.py` — método `TimelinePlotter.plot()`

CSVs de voo a 8 Hz com >45 min geram ~21.600 pontos por variável. O browser não renderiza mais de ~5.000 pontos com fluidez.

```python
_MAX_POINTS = 4_000  # threshold de decimação

def _downsample(series: pd.Series, time: pd.Series, max_pts: int = _MAX_POINTS):
    """Decimação LTTB (Largest Triangle Three Buckets) ou simple stride."""
    if len(series) <= max_pts:
        return time, series
    stride = max(1, len(series) // max_pts)
    return time.iloc[::stride], series.iloc[::stride]
```

Aplicar antes de `fig.add_trace()` dentro do loop de `plot()`. Manter `customdata` com valores reais (não decimados) **não** é possível neste modelo — alternativa: exibir valor real via `snapshot` do slider (já feito pelos cards de Subsistemas).

**Ganho estimado:** ~60% de redução no tempo de serialização JSON → browser.

---

#### A.3 — Eliminar `st.rerun()` do slider via callback

**Arquivo:** `src/ui/components/__init__.py` — `TimeController.render_slider()`

O `st.rerun()` no `on_change` do slider é necessário para sincronizar os painéis abaixo. Porém, é possível substituí-lo por um mecanismo de callback nativo do Streamlit:

```python
def _on_slider_change(self):
    """Callback do slider — atualiza estado sem rerun desnecessário."""
    st.session_state[self.SESSION_KEY] = st.session_state[f"{self.SESSION_KEY}_widget"]

idx = st.slider(
    "Linha do Tempo",
    min_value=0,
    max_value=n - 1,
    value=current_idx,
    key=f"{self.SESSION_KEY}_widget",
    label_visibility="collapsed",
    on_change=self._on_slider_change,   # ← callback nativo, sem rerun explícito
)
```

Com `on_change`, o Streamlit executa apenas o callback e re-renderiza somente os widgets afetados, sem re-executar o script inteiro do início.

> [!IMPORTANT]
> Testar compatibilidade com a versão atual do Streamlit (`>=1.32`). O `on_change` com métodos de instância pode exigir uso de `functools.partial`.

---

### Fase B — Separação do Layout (médio prazo)

#### B.1 — Fragmentação via `@st.fragment`

**Arquivo:** `src/ui/views/vadr.py`

O Streamlit 1.33+ suporta `@st.fragment` para isolar seções do layout que podem re-renderizar independentemente:

```python
@st.fragment
def _render_time_section(df, y_cols, fault_columns):
    """Fragment isolado: slider + gráfico. Re-renderiza sem afetar os cards abaixo."""
    controller = TimeController(df)
    t_idx = int(st.session_state.get(TimeController.SESSION_KEY, 0))
    snapshot = controller.get_snapshot(t_idx)
    fig = copy.deepcopy(build_base_figure(df, tuple(y_cols), tuple(fault_columns)))
    t_cursor = float(snapshot["TIME"]) if "TIME" in snapshot else 0
    fig.add_vline(x=t_cursor, ...)
    st.plotly_chart(fig, use_container_width=True)
    controller.render_slider()
    return snapshot

@st.fragment
def _render_panels_section(snapshot, fault_columns):
    """Fragment isolado: cards de atitude, subsistemas e mapa."""
    attitude_box.render(snapshot, fault_columns)
    subsys_cards.render_all(snapshot)
    _FLIGHT_MAP.render(df, snapshot)
```

Com `@st.fragment`, mover o slider re-executa apenas `_render_time_section` sem tocar nos cards abaixo — e vice-versa ao interagir com o mapa.

---

### Fase C — Otimizações Adicionais (longo prazo)

#### C.1 — Cursor via Plotly `relayoutData` (sem rerun)

Substituir `fig.add_vline()` + `st.plotly_chart()` por uma atualização de layout via `plotly_events` ou `st.components.v1.html` com JavaScript puro para mover o cursor sem rerun algum.

#### C.2 — Exportar gráfico estático após zoom

Ao usuário fazer zoom numa janela temporal < 30% do total, re-amostrar em alta resolução apenas a janela visível.

#### C.3 — Worker de pré-processamento

Pré-calcular a figura base em background thread (`concurrent.futures`) durante o carregamento do CSV, armazenando em `st.session_state["base_fig"]`.

---

## Ordem de Implementação Recomendada

| Prioridade | Item | Esforço | Ganho |
|-----------|------|---------|-------|
| 🔴 1 | A.1 — Cache com `@st.cache_data` | Baixo | 80% |
| 🔴 2 | A.2 — Decimação de pontos | Médio | 60% |
| 🟠 3 | A.3 — Callback nativo do slider | Baixo | 30% |
| 🟡 4 | B.1 — Fragmentos `@st.fragment` | Médio | 50% |
| 🟢 5 | C.1 — Cursor via JS | Alto | 90% |
| 🟢 6 | C.2 — Zoom adaptativo | Alto | 40% |

> [!NOTE]
> Implementar A.1 + A.2 já resolve a queixa principal. As fases B e C são melhorias arquiteturais para uma versão futura com exigência de tempo real.

---

## Referências de Código

- `src/ui/views/vadr.py` L.124-144 — loop de construção do gráfico
- `src/ui/plots.py` L.107-213 — `TimelinePlotter.plot()`
- `src/ui/components/__init__.py` L.140-163 — `TimeController.render_slider()`
- [Streamlit `@st.cache_data` docs](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data)
- [Streamlit `@st.fragment` docs](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment)
