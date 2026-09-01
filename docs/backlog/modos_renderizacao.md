# Backlog: Modos de Renderização (Desempenho / Compatibilidade)

**Criado em:** 2026-09-01
**Origem:** discussão sobre fluidez e precisão do gráfico de Análise Temporal, após a implementação do playback (RF05.1).
**Documentos relacionados:** `docs/backlog/resolvidos/correcao_grafico.md` (Fases A/B já concluídas), `docs/RETOMADA.md` §13.

---

## 🎯 Motivação

O playback atual roda a **5 FPS** e esse é praticamente o teto do modelo server-side. Cada quadro exige: rerun do Python → re-serialização da figura Plotly → transferência → re-render no navegador. Isso tem piso de dezenas de milissegundos; 60 FPS exigiria ~16 ms por quadro **no total**. Não é problema de otimização, é limite de arquitetura.

Além da fluidez, existe um **problema de precisão** já presente hoje: a decimação usa *stride* uniforme (1 a cada N amostras), o que **descarta picos estreitos** — justamente os transientes que interessam numa análise de voo (um over-G de meio segundo, um input abrupto de comando). O próprio `correcao_grafico.md` (A.2) registra a ressalva: *"LTTB pode ser avaliado depois se picos estreitos forem perdidos"*.

### Fatos levantados

| Fato | Valor | Consequência |
|------|-------|--------------|
| Taxa de amostragem dos dados | **8 Hz** (0,125 s) | 60 FPS exige **interpolação** entre amostras (7,5 quadros de tela por amostra real), não mais dados |
| Amostras de um voo real | 46.629 (~97 min) | 1 série em Float32 = 182 KB; 20 séries = 3,6 MB → cabe todo na memória do navegador |
| `plotly.js` no pacote Python | 4,3 MB, via `plotly.offline.get_plotlyjs()` | Client-side é viável **100% offline**, sem CDN e sem build npm |
| Uniformidade do `TIME` | Perfeitamente uniforme | Índice e tempo são proporcionais — slider e cursor podem ser mapeados linearmente |

---

## 🧭 Os dois modos

| | ⚡ **Desempenho** | 🛡️ **Compatibilidade** |
|---|---|---|
| Traço do gráfico | `go.Scattergl` (WebGL) | `go.Scatter` (SVG) — comportamento atual |
| Orçamento de pontos | Amostras cheias (sem decimar) | Envelope reduzido (~6.000 pontos) |
| Playback | 60 FPS client-side *(Etapa 2)* | 5 FPS server-side (atual) |
| Seguir cursor / zoom sincronizado | Sim *(Etapa 2)* | Não |
| Requisito | WebGL disponível no navegador | Nenhum |

> ⚠️ **Decisão de produto a assumir explicitamente:** os modos **não serão equivalentes em funcionalidade**. Seguir-cursor e zoom sincronizado existirão apenas no modo Desempenho. O modo Compatibilidade é um *fallback degradado*, não um espelho. Sem essa decisão registrada, isso vira suporte recorrente do tipo *"por que na minha máquina não tem esse recurso?"*.

---

## 🏛️ Fronteira arquitetural

O risco principal de ter dois modos é duplicar a manutenção. Para evitar isso, a divergência precisa ficar atrás de **uma única fronteira**:

```
render_main()
├── metadados, seletor de variáveis, excedência    [COMPARTILHADO]
├── ► VIEWPORT ◄                                    ← única divergência
│     ├── Compatibilidade: Plotly server-side + slider + rerun de fragmento
│     └── Desempenho:      Scattergl (Etapa 1) → componente JS (Etapa 2)
├── AttitudeBox / SubsystemCards                    [COMPARTILHADO até a Etapa 3]
└── render_bottom_panel()                           [COMPARTILHADO]
```

**Regra:** a decimação min/máx é **compartilhada pelos dois modos**. Ela trata de precisão do sinal, não de tecnologia de renderização. Apenas o *orçamento* de pontos muda entre os modos.

---

## 🔨 Etapa 1 — Seletor + Scattergl + envelope min/máx

**Branch sugerida:** `feature/render-modes-etapa1`
**Custo:** baixo. **Sem JavaScript.**
**Entrega:** precisão real (nenhum pico perdido) nos dois modos + gráfico bem mais leve no modo Desempenho.

### Arquivos afetados

| Arquivo | Mudança |
|---------|---------|
| `src/data/decimation.py` | **Novo** — algoritmo de envelope min/máx |
| `src/ui/plots.py` | `TimelinePlotter.plot()` recebe `render_mode`; escolhe `Scatter`/`Scattergl` e o orçamento de pontos |
| `src/ui/views/landing.py` | Rádio de seleção do modo, ao lado do "Análise Básica/Completa" já existente |
| `src/ui/views/vadr.py` | Lê `st.session_state.render_mode` e repassa a `build_base_figure()` |
| `tests/test_decimation.py` | **Novo** — testes do envelope |

### O algoritmo (o núcleo da etapa)

Substituir o *stride* por **envelope min/máx por bucket**: para cada faixa de amostras que caberia em uma coluna de pixels, emitir o **mínimo e o máximo** daquela faixa. É o que osciloscópios e editores de áudio fazem — nenhum pico desaparece, independentemente do zoom.

```python
def minmax_envelope(x: np.ndarray, y: np.ndarray, max_points: int) -> tuple[np.ndarray, np.ndarray]:
    """Decima preservando extremos. Cada bucket contribui com 2 pontos (min e max)."""
    n = len(y)
    if n <= max_points:
        return x, y

    n_buckets = max(1, max_points // 2)          # cada bucket gera 2 pontos
    buckets = np.array_split(np.arange(n), n_buckets)

    out_idx = []
    for b in buckets:
        yb = y[b]
        if np.all(np.isnan(yb)):                 # bucket totalmente vazio
            continue
        i_min = b[np.nanargmin(yb)]
        i_max = b[np.nanargmax(yb)]
        # Emite em ordem temporal para não criar zigue-zague artificial na linha
        out_idx.extend(sorted((i_min, i_max)))

    out_idx = np.array(out_idx)
    return x[out_idx], y[out_idx]
```

**Cuidados de implementação:**
- `np.nanargmin`/`nanargmax` **lançam exceção** em bucket totalmente NaN — daí o guard `np.all(np.isnan(...))`.
- Emitir em **ordem temporal** (`sorted`), não sempre min-antes-de-max, para não introduzir zigue-zague que não existe no sinal.
- **Mudança estrutural:** hoje o código decima o DataFrame inteiro uma vez (`plot_df = _downsample_frame(df)`) e reaproveita `plot_df[time_column]` para todas as séries. Com envelope **por série**, cada traço passa a ter seu próprio eixo X. Os traços são independentes no Plotly, então isso funciona — mas é uma mudança real na estrutura de `TimelinePlotter.plot()`.
- Marcadores de falha (`add_fault_markers`) usam `df.loc[fault_mask]` em resolução cheia e **não são afetados**.

### Sobre o `Scattergl`

Ganho: renderização por WebGL, aguenta as 46 mil amostras sem decimar.

⚠️ **Validar antes de dar por pronto** — o `Scattergl` não é 100% idêntico ao `Scatter`:
- `connectgaps=True` (usado para variáveis sub-rate)
- `dash="dot"` (usado nas séries constantes)
- Anti-aliasing e espessura de linha renderizam de forma um pouco diferente

Não usar `Scattergl` em todos os gráficos: navegadores limitam o número de contextos WebGL simultâneos (~8-16). **Apenas o gráfico temporal.**

### Seleção na landing page

Rádio no mesmo bloco do seletor "Análise Básica/Completa" que já existe (`landing.py`, ~linha 80), guardado em `st.session_state.render_mode`, exatamente como `analysis_mode`.

Na Etapa 1 a seleção é **manual**, com texto de ajuda do tipo *"Se o gráfico não aparecer, troque para Compatibilidade"*. Detecção automática de WebGL exige JS reportando ao Python — só faz sentido a partir da Etapa 2.

### Critérios de aceite

- [ ] Um pico de 1 amostra (ex.: `NZ` de 4,5 G em 0,125 s) permanece visível no gráfico com o voo inteiro na tela, nos **dois** modos
- [ ] Modo Desempenho renderiza 46 k amostras sem travar
- [ ] Modo Compatibilidade mantém o comportamento atual, sem regressão
- [ ] Séries constantes (ex.: `PCL` fixo) continuam visíveis com `connectgaps`
- [ ] Escolha do modo persiste ao trocar de arquivo pelo painel inferior
- [ ] `tests/test_decimation.py` cobre: preservação de pico, bucket com NaN, série menor que o orçamento, ordem temporal

---

## 🔨 Etapa 2 — Viewport client-side (60 FPS)

**Branch sugerida:** `feature/viewport-clientside`
**Custo:** médio. **Depende da Etapa 1.**
**Entrega:** playback e scrub a 60 FPS + zoom com re-decimação + seguir-cursor.

### Como embutir o Plotly offline

Sem CDN e sem npm — o JS já vem no pacote Python:

```python
import plotly.offline
plotly_js = plotly.offline.get_plotlyjs()   # 4,3 MB de JS, embutido no .html
```

### Estrutura

Um componente autocontido via `st.components.v1.declare_component` (com pasta estática escrita à mão — **não precisa de build npm**) ou `st.components.v1.html` se a comunicação de volta não for necessária.

**Contrato de dados (Python → JS), enviado uma vez por arquivo/seleção:**

```jsonc
{
  "time":     "<Float32Array base64>",        // eixo temporal, segundos
  "series":   { "BALT": "<base64>", "NZ": "<base64>", ... },
  "discrete": ["WOW", "LDG", "ENGFIRE"],      // sinais que NÃO podem ser interpolados
  "fps": 60,
  "playback_target_sec": 60
}
```

### Onde a fluidez realmente vem

1. O gráfico é desenhado **uma única vez**.
2. O cursor **sai de dentro da figura** e vira um `div` posicionado por CSS sobre o gráfico — mover é `style.transform`, custo praticamente zero.
3. Loop com `requestAnimationFrame`, interpolando entre amostras.

### Regras de interpolação (correção, não estética)

> Esta seção é a mais importante da Etapa 2. Interpolar errado faz a UI **inventar dados que o gravador nunca registrou**.

| Tipo de sinal | Exemplos | Regra |
|---------------|----------|-------|
| **Analógico** | `APA`, `ARA`, `BALT`, `MACH`, `NZ`, `AOA`, `ITT`, `FF`, `NG`, `NP`, `Q`, `PCL` | Interpolação linear entre amostras |
| **Discreto / booleano** | `WOW`, `LDG`, `ENGFIRE`, `CANOPY`, flags `MW*_*` | **Step-hold** (amostra anterior). Nunca interpolar — criaria estados intermediários inexistentes |
| **Angular com wraparound** | `MAG_HDG` | Interpolar pelo **arco mais curto**, senão 359° → 1° vira uma volta completa para trás |

**Regra de ouro:** *suavizar a imagem, não os números.* Ponteiros e horizonte podem interpolar; os **valores numéricos exibidos** devem ser a amostra real mais próxima — senão o analista lê na tela um número que não existe no gravador.

### Sincronização com os instrumentos (que continuam server-side nesta etapa)

O componente reporta a posição ao Python numa taxa **reduzida (2-4 Hz)**. Cada reporte dispara um rerun do fragmento, que redesenha **apenas os instrumentos** — o componente não é recriado, porque suas *props* não mudaram. Resultado: gráfico fluido a 60 FPS, instrumentos acompanhando a alguns Hz, sem piscar.

### Zoom e seguir-cursor

Em JS temos acesso aos eventos `plotly_relayout` — o que **o Streamlit não expõe ao Python** (limitação registrada em B.3 de `correcao_grafico.md`). Isso destrava, só no modo Desempenho:
- Re-decimação por nível de zoom (mais detalhe conforme aproxima, até amostras cruas)
- Slider mapeado à janela visível em vez do voo inteiro
- Pan automático acompanhando o cursor durante o playback

### Critérios de aceite

- [ ] Playback visualmente fluido (sem cintilação) num voo de ~97 min
- [ ] Cursor acompanha o playback sem sair da janela ampliada
- [ ] Zoom aproxima até a amostra crua, sem perder pico
- [ ] Sinais discretos **não** interpolam (verificar `WOW` numa transição solo/ar)
- [ ] Valores numéricos exibidos batem com a amostra do CSV, não com o valor interpolado
- [ ] Trocar para modo Compatibilidade continua funcionando sem resíduo de estado

### Riscos

- **Não é testável por `AppTest`.** O framework cobre o lado Python e as props enviadas, mas **não executa o JS**. A validação de comportamento depende de teste manual no navegador.
- Memória do navegador em voos muito longos — daí o modo Compatibilidade como escape.

---

## 🔨 Etapa 3 — Instrumentos em SVG dentro do componente

**Branch sugerida:** `feature/instrumentos-svg`
**Custo:** alto. **Só executar se as Etapas 1 e 2 se provarem.**
**Entrega:** tudo sincronizado a 60 FPS, incluindo horizonte, gauges e cards.

Os instrumentos são baratos em SVG: o horizonte artificial é um `rotate`+`translate`; um ponteiro de gauge é um `rotate`. Atualizar isso 60x/s é trivial — muito mais barato que redesenhar figuras Plotly.

> ⚠️ **Condição para executar:** esta etapa cria **duplicação real** — duas implementações dos mesmos instrumentos (Python/Plotly e JS/SVG). Só vale a pena se a versão JS **substituir** a Python no modo VADR, não conviver com ela. Caso contrário, toda mudança de instrumento passa a exigir manutenção em dois lugares.

Componentes a portar: `AttitudeIndicator` (`plots.py`), `EngineGaugePlotter` (`plots.py`), `SubsystemCards` e `AttitudeBox` (`components/__init__.py`).

---

## 🗂️ Pré-análise no carregamento (opcional, complementa a Etapa 1)

Ideia levantada na mesma discussão: gerar, **uma vez por arquivo na ingestão**, uma **pirâmide multi-resolução** dos envelopes min/máx (conceito de *mipmap* de editor de áudio) e salvá-la junto do Parquet.

**Benefício:** qualquer nível de zoom passa a ser servido instantaneamente e com precisão, sem recalcular envelope a cada interação — vale para os dois modos.

**Custo:** aumenta o tempo de ingestão e o tamanho do cache em disco. Avaliar só se a decimação sob demanda da Etapa 1 se mostrar lenta na prática — **não implementar preventivamente.**

---

## 🌿 Sequenciamento e branches

Partindo de `development` (fluxo main + development adotado em 01/09/2026):

| Ordem | Branch | Depende de | Risco |
|-------|--------|------------|-------|
| 1 | `feature/render-modes-etapa1` | — | Baixo |
| 2 | `feature/viewport-clientside` | Etapa 1 | Médio |
| 3 | `feature/instrumentos-svg` | Etapa 2 | Alto |

Cada uma volta para `development` por merge; `main` avança apenas em pontos de release.

**Recomendação:** executar a Etapa 1 e **medir** antes de decidir sobre a Etapa 2. Ela sozinha já ataca a prioridade declarada (precisão acima de estética) e estabelece a fronteira arquitetural correta, sem comprometer nada das etapas seguintes.
