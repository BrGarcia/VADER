# Plano de Correção - Fluidez do Gráfico "Análise Temporal"

**Data:** 2026-05-19  
**Arquivos de referência:** `src/ui/views/vadr.py`, `src/ui/plots.py`, `src/ui/components/__init__.py`  
**Sintoma:** Ao mover o slider de tempo, a aplicação demora visivelmente para atualizar, pois reconstrói e reenvia o gráfico Plotly completo, além de recalcular os painéis dependentes do instante selecionado.

**Premissa de uso:** aplicação local/monousuário. Não é necessário projetar isolamento complexo entre múltiplos usuários ou sessões concorrentes.

---

## Diagnóstico da Causa-Raiz

### Fluxo atual problemático

```text
Usuário move o slider
        ↓
st.slider dispara rerun do Streamlit
        ↓
TimeController.render_slider() também chama st.rerun()
        ↓
render_main() é chamado novamente
        ↓
_PLOTTER.plot()              reconstrói traces com todos os pontos
_PLOTTER.add_phase_bands()   recria faixas de fase
_PLOTTER.add_fault_markers() recria marcadores de falha
fig.add_vline()              adiciona cursor dentro da figura completa
        ↓
st.plotly_chart() serializa a figura inteira para o browser
        ↓
AttitudeBox.render()
SubsystemCards.render_all()
FlightMap.render()
```

**Problema central:** o gráfico temporal é recriado do zero e reenviado ao browser a cada movimento do slider. Para arquivos maiores, isso combina custo Python, custo de serialização JSON e custo de renderização no Plotly do navegador.

Além disso, o `st.rerun()` explícito dentro de `TimeController.render_slider()` tende a ser redundante: widgets Streamlit já disparam rerun quando seu valor muda. O `st.rerun()` manual pode acrescentar reruns extras ou tornar a interação mais custosa do que necessário.

### Problemas identificados

| # | Local | Problema | Impacto |
|---|-------|----------|---------|
| P-01 | `TimeController.render_slider()` | `st.rerun()` explícito após mudança do slider | Alto |
| P-02 | `vadr.py` | `plot()`, `add_phase_bands()` e `add_fault_markers()` chamados em todo rerun | Alto |
| P-03 | `TimelinePlotter.plot()` | Dados completos enviados ao Plotly sem decimação | Alto |
| P-04 | `vadr.py` | `fig.add_vline()` altera a figura completa a cada tick | Médio |
| P-05 | `st.plotly_chart()` | Figura grande serializada novamente para o browser | Médio |
| P-06 | `add_fault_markers()` | Marcadores usam valor real enquanto as séries são normalizadas para 5-95 | Médio |

---

## Observações Importantes sobre Streamlit

### `on_change` não evita rerun completo

Usar `on_change` no `st.slider()` é uma melhoria válida para organizar estado e remover o `st.rerun()` manual, mas **não isola a atualização do widget**. Em Streamlit, callbacks de widgets rodam antes da próxima execução do script; depois disso, o script reexecuta normalmente.

Portanto:

- remover `st.rerun()` do slider deve reduzir trabalho redundante;
- `on_change` não deve ser tratado como renderização parcial;
- o ganho real virá principalmente de cache, redução de pontos e separação entre gráfico base e cursor.

### Cache direto do DataFrame pode ter custo

`@st.cache_data` consegue cachear funções que recebem `pd.DataFrame`, mas DataFrames grandes precisam ser hasheados/serializados para validação do cache. Para arquivos de cerca de 10 MB isso tende a ser aceitável, mas a solução fica mais robusta se o cache usar uma chave leve, como:

- nome do arquivo atual;
- tamanho ou timestamp do arquivo;
- fingerprint calculado na ingestão;
- colunas selecionadas;
- colunas de falha disponíveis.

---

## Abordagem Recomendada

Implementar uma **Fase A revisada**, focada nos ganhos de menor risco:

1. Remover o `st.rerun()` explícito do slider.
2. Reduzir a quantidade de pontos enviados ao Plotly.
3. Cachear/preparar o gráfico base sem cursor.
4. Adicionar o cursor apenas no final, sem poluir o cache.
5. Corrigir a escala dos marcadores de falha para usar a mesma normalização das séries.
6. Adicionar modo de carregamento **Análise Básica / Análise Completa**.

As fases com `@st.fragment` ou JavaScript devem ficar para depois de medir o resultado dessas mudanças. Em uma aplicação monousuário, a prioridade deve ser manter o fluxo simples: estado em `st.session_state`, cache local e Parquet separado por modo de carregamento quando necessário.

---

## Fase A - Correção Recomendada

### A.1 - Remover `st.rerun()` manual do slider

**Arquivo:** `src/ui/components/__init__.py`  
**Classe:** `TimeController`

O slider já atualiza `st.session_state` e dispara rerun. A implementação deve evitar um segundo rerun explícito.

Exemplo simples:

```python
idx = st.slider(
    "Linha do Tempo",
    min_value=0,
    max_value=n - 1,
    value=current_idx,
    key=f"{self.SESSION_KEY}_widget",
    label_visibility="collapsed",
)

st.session_state[self.SESSION_KEY] = int(idx)
return int(idx)
```

Alternativa com callback:

```python
def _sync_slider_state(self) -> None:
    st.session_state[self.SESSION_KEY] = int(
        st.session_state.get(f"{self.SESSION_KEY}_widget", 0)
    )

idx = st.slider(
    "Linha do Tempo",
    min_value=0,
    max_value=n - 1,
    value=current_idx,
    key=f"{self.SESSION_KEY}_widget",
    label_visibility="collapsed",
    on_change=self._sync_slider_state,
)
```

**Nota:** a versão com callback melhora a organização do estado, mas não elimina rerun completo do Streamlit.

---

### A.2 - Decimar séries temporais antes do Plotly

**Arquivo:** `src/ui/plots.py`  
**Método:** `TimelinePlotter.plot()`

O Plotly não precisa receber todos os pontos para manter boa leitura visual em uma janela de 900-1400 px. Limitar cada série para algo entre `4_000` e `8_000` pontos reduz serialização, tráfego interno e custo de renderização no browser.

Implementação inicial recomendada: stride simples.

```python
_MAX_TIMELINE_POINTS = 6_000

def _downsample_frame(df: pd.DataFrame, max_points: int = _MAX_TIMELINE_POINTS) -> pd.DataFrame:
    if len(df) <= max_points:
        return df

    stride = max(1, math.ceil(len(df) / max_points))
    return df.iloc[::stride]
```

Aplicar antes de `fig.add_trace()`:

```python
plot_df = _downsample_frame(df)

fig.add_trace(go.Scatter(
    x=plot_df[time_column],
    y=normalized.loc[plot_df.index],
    customdata=series.loc[plot_df.index].to_numpy(),
    ...
))
```

Para uma primeira correção, stride é suficiente. LTTB pode ser avaliado depois se a visualização precisar preservar melhor picos estreitos.

---

### A.3 - Separar preparação de dados e construção do gráfico base

**Arquivos:** `src/ui/plots.py`, `src/ui/views/vadr.py`

O ideal é cachear uma representação leve ou uma figura base sem cursor. Duas opções são aceitáveis:

#### Opção 1 - Cachear figura base

Mais simples de implementar:

```python
@st.cache_data(show_spinner=False)
def build_base_figure(
    df: pd.DataFrame,
    y_cols: tuple[str, ...],
    fault_columns: tuple[str, ...],
) -> go.Figure:
    plotter = TimelinePlotter()
    fig = plotter.plot(df, list(y_cols))
    fig = plotter.add_phase_bands(fig, df)
    fig = plotter.add_fault_markers(fig, df, list(fault_columns), y_column=list(y_cols))
    return fig
```

Uso:

```python
import copy

base_fig = build_base_figure(df, tuple(y_cols), tuple(fault_columns))
fig = copy.deepcopy(base_fig)
fig.add_vline(...)
st.plotly_chart(fig, ...)
```

Essa opção resolve o rebuild Python, mas ainda exige cuidado com o custo de hash do DataFrame.

#### Opção 2 - Cachear dados preparados por chave leve

Mais robusta para crescer:

```python
@st.cache_data(show_spinner=False)
def prepare_timeline_data(
    file_key: str,
    y_cols: tuple[str, ...],
    fault_columns: tuple[str, ...],
) -> dict:
    ...
```

Nesta opção, `file_key` deve representar o dataset atual. O DataFrame pode ser recuperado de `st.session_state.current_df` dentro da função chamadora, ou a ingestão pode registrar uma chave estável em `df.attrs`.

**Recomendação pragmática:** começar pela Opção 1 se o dataset típico for pequeno/médio. Migrar para Opção 2 se a medição mostrar custo relevante de cache/hash.

---

### A.4 - Manter cursor fora do gráfico base

**Arquivo:** `src/ui/views/vadr.py`

O cursor temporal muda a cada movimento do slider; traces, faixas de fase e marcadores não. Portanto o cursor deve ser aplicado somente depois de obter o gráfico base cacheado.

```python
base_fig = build_base_figure(...)
fig = copy.deepcopy(base_fig)

fig.add_vline(
    x=t_cursor,
    line=dict(color="#FF4B4B", width=2, dash="dash"),
    annotation_text=f"  t={t_cursor:.2f}s",
    annotation_font=dict(color="#FF4B4B", size=11),
)
```

Essa separação impede que o cursor contamine o cache da figura base.

---

### A.5 - Corrigir escala dos marcadores de falha

**Arquivo:** `src/ui/plots.py`  
**Método:** `TimelinePlotter.add_fault_markers()`

Hoje as séries principais são normalizadas para a escala visual `5-95`, mas os marcadores de falha usam valores reais da variável de referência. Isso pode posicionar os marcadores fora da faixa visível ou desalinhados da curva.

Ao adicionar marcadores, calcular o mesmo valor normalizado da série de referência:

```python
ref_series = df[y_ref]
ref_clean = ref_series.dropna()
v_min, v_max = float(ref_clean.min()), float(ref_clean.max())

if (v_max - v_min) < 1e-6:
    y_marker = fault_rows[y_ref] * 0.0 + 8.0
else:
    y_marker = 5.0 + (fault_rows[y_ref] - v_min) / (v_max - v_min) * 90.0
```

Manter o hover com o valor real:

```python
customdata=fault_rows[y_ref].to_numpy()
hovertemplate=f"<b>FALHA: {short_name}</b><br>t=%{{x:.3f}} s<br>{y_ref}=%{{customdata}}<extra></extra>"
```

---

### A.6 - Adicionar modo Análise Básica / Análise Completa

**Arquivos prováveis:** `src/ui/views/landing.py`, `src/data/data_loader.py`, `src/ui/views/vadr.py`

Adicionar na página de carregamento um seletor de modo:

- **Análise Básica:** carrega apenas as variáveis necessárias para a tela principal e para uma análise rápida.
- **Análise Completa:** carrega todas as 258 variáveis do CSV.

Como a aplicação é monousuário, a implementação pode ser simples: guardar o modo escolhido em `st.session_state` e repassar esse modo para o `DataLoader.ingest()`. Não há necessidade de controle por usuário, permissões ou cache distribuído.

#### Variáveis recomendadas para Análise Básica

Manter 28 variáveis originais do CSV:

```text
TIME
STIME
GPSLAT
GPSLONG
BALT
PALT
RAD_ALT
MACH
AOA
APA
ARA
NZ
MAG_HDG
WOW
LDG
FLAP
AIRBRK
PCL
Q
ITT
NG
NP
FF
OT
OP
ENGFIRE
MWC_DATA
VALIDARINC
```

Além dessas, o DataFrame processado pode continuar contendo colunas derivadas internas:

```text
TIME_STR
PHASE
```

Essas duas não precisam estar no CSV original filtrado; podem ser criadas no pipeline atual:

- `TIME_STR` em `_resolve_time_column()`;
- `PHASE` em `_coerce_types()`, derivada de `WOW`.

#### Cobertura da Análise Básica

As 28 variáveis atendem ao fluxo principal atual:

| Área | Variáveis cobertas |
|------|--------------------|
| Linha do tempo | `TIME`, `STIME`, `TIME_STR` |
| Mapa | `GPSLAT`, `GPSLONG`, `MAG_HDG` |
| Atitude e Dados Críticos | `APA`, `ARA`, `BALT`, `PALT`, `MACH`, `NZ`, `AOA` |
| Motor | `Q`, `ITT`, `NG`, `NP`, `FF`, `OT`, `OP`, `PCL` |
| Subsistemas | `LDG`, `WOW`, `NZ`, `ITT`, `FF`, `NG`, `PCL` |
| Fase de voo | `WOW`, `PHASE` |
| Alertas principais | `ENGFIRE`, `MWC_DATA`, `VALIDARINC` |

#### Limitações esperadas da Análise Básica

A Análise Básica não deve carregar as colunas detalhadas `MW1_*`, `MW2_*`, `MW3_*`. Consequências:

- `_LOADER.get_fault_columns(df)` deve retornar uma lista vazia ou reduzida;
- marcadores detalhados de falha no gráfico podem desaparecer;
- o painel de alertas continua funcionando para mensagens derivadas de `MWC_DATA`;
- investigação profunda de falhas PMU/MW exige Análise Completa.

Esse comportamento é aceitável para um modo básico, desde que a UI deixe claro que ele prioriza fluidez e dados essenciais.

#### Estratégia de implementação no `DataLoader`

Adicionar uma constante:

```python
BASIC_ANALYSIS_COLUMNS = [
    "TIME", "STIME", "GPSLAT", "GPSLONG",
    "BALT", "PALT", "RAD_ALT", "MACH", "AOA", "APA", "ARA", "NZ", "MAG_HDG",
    "WOW", "LDG", "FLAP", "AIRBRK",
    "PCL", "Q", "ITT", "NG", "NP", "FF", "OT", "OP",
    "ENGFIRE", "MWC_DATA", "VALIDARINC",
]
```

Atualizar a leitura do CSV para aceitar um modo:

```python
def ingest(self, filepath: str, analysis_mode: str = "basic") -> pd.DataFrame:
    ...
```

Na leitura bruta:

```python
usecols = BASIC_ANALYSIS_COLUMNS if analysis_mode == "basic" else None

df = pd.read_csv(
    filepath,
    skiprows=skip_rows,
    header=0,
    usecols=lambda c: c.strip() in usecols if usecols else True,
    low_memory=False,
    na_values=["", " "],
    keep_default_na=True,
)
```

Preferir `usecols` no `read_csv()` em vez de carregar tudo e filtrar depois. Isso reduz custo de parsing, memória e tempo de ingestão.

#### Cache/Parquet por modo

Para evitar conflito entre Parquet básico e completo, o caminho processado deve incluir o modo:

```text
data/processed/<nome>__basic.parquet
data/processed/<nome>__complete.parquet
```

ou equivalente:

```python
def _get_parquet_path(self, csv_filepath: str, analysis_mode: str = "basic") -> str:
    basename = os.path.splitext(os.path.basename(csv_filepath))[0]
    return os.path.join(self.processed_dir, f"{basename}__{analysis_mode}.parquet")
```

Em contexto monousuário, isso é suficiente. Não há necessidade de invalidadores por usuário ou namespace de sessão.

#### UI recomendada

Na página de carregamento, adicionar uma escolha simples:

```python
analysis_mode = st.radio(
    "Tipo de análise",
    options=["basic", "complete"],
    format_func=lambda value: "Análise Básica" if value == "basic" else "Análise Completa",
    horizontal=True,
)
```

Guardar:

```python
st.session_state.analysis_mode = analysis_mode
```

E chamar:

```python
df = _LOADER.ingest(raw_path, analysis_mode=analysis_mode)
```

#### Ganho esperado

O modo básico reduz o CSV lógico de 258 para 28 variáveis originais, aproximadamente **89% menos colunas**.

Ganhos esperados:

- menor tempo de carregamento do CSV;
- menor uso de memória;
- menor tempo de coerção numérica;
- Parquet processado menor;
- seletor de variáveis mais leve;
- menor risco de o usuário selecionar séries irrelevantes e pesadas no gráfico.

Esse ganho é complementar às melhorias de gráfico. Ele ajuda principalmente no carregamento e na navegação geral; a fluidez do slider ainda depende de downsampling, cache do gráfico base e remoção do `st.rerun()` manual.

---

## Fase B - Melhorias Após Medição

### B.1 - `@st.fragment`

`@st.fragment` pode ajudar a reduzir o escopo de rerenders em versões modernas do Streamlit, mas deve ser tratado como melhoria posterior. Antes de introduzir fragmentos, confirmar:

- versão real do Streamlit no projeto;
- compatibilidade com os componentes usados;
- comportamento do estado compartilhado entre gráfico, slider, cards e mapa.

Possível divisão futura:

- fragmento para gráfico + slider;
- fragmento para painéis derivados do snapshot;
- fragmento para mapa, se ele continuar pesado.

### B.2 - Cursor via JavaScript/Plotly relayout

Se ainda houver exigência de interação quase em tempo real, mover o cursor no browser sem rerun é a solução mais fluida. Isso exige `st.components.v1.html`, componente customizado ou biblioteca de eventos Plotly.

Essa opção tem maior custo de manutenção e deve ser usada apenas se a Fase A não for suficiente.

### B.3 - Downsampling adaptativo por zoom

Em uma versão futura, o gráfico pode renderizar uma versão reduzida para visão global e recalcular uma série mais detalhada quando o usuário der zoom em uma janela temporal menor.

---

## Ordem de Implementação Recomendada

| Prioridade | Item | Esforço | Ganho esperado |
|------------|------|---------|----------------|
| 1 | A.1 - Remover `st.rerun()` manual do slider | Baixo | Médio |
| 2 | A.2 - Decimação de pontos | Baixo/Médio | Alto |
| 3 | A.3 - Cachear/preparar gráfico base | Médio | Alto |
| 4 | A.4 - Cursor fora do gráfico base | Baixo | Médio |
| 5 | A.5 - Corrigir escala dos marcadores de falha | Baixo | Correção visual |
| 6 | A.6 - Modo Análise Básica / Completa | Médio | Alto no carregamento |
| 7 | B.1 - Avaliar `@st.fragment` | Médio | Variável |
| 8 | B.2 - Cursor via JS/relayout | Alto | Muito alto |

---

## Critério de Aceite

Após a Fase A, validar com um CSV representativo:

- mover o slider não deve apresentar travamentos perceptíveis;
- o gráfico deve manter leitura visual equivalente;
- hover deve continuar mostrando valores reais;
- marcadores de falha devem aparecer alinhados à curva normalizada;
- troca de variáveis deve reconstruir o gráfico corretamente;
- zoom horizontal deve continuar funcionando com `scrollZoom`;
- Análise Básica deve carregar apenas as 28 variáveis originais previstas, mais derivadas internas como `TIME_STR` e `PHASE`;
- Análise Completa deve continuar carregando as 258 variáveis originais.

Medições úteis:

- tempo médio de rerun após mover slider;
- tamanho do JSON enviado ao Plotly;
- número de pontos por trace;
- tempo de renderização percebido no browser.

---

## Referências de Código

- `src/ui/views/vadr.py` - construção e renderização do gráfico principal
- `src/ui/plots.py` - `TimelinePlotter.plot()`, `add_phase_bands()`, `add_fault_markers()`
- `src/ui/components/__init__.py` - `TimeController.render_slider()`
- Streamlit `st.cache_data`: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data
- Streamlit `st.fragment`: https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment
