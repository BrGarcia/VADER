# ROADMAP — V.A.D.E.R.
**Visualizador Analítico de Dados de Engenharia e Rastreio**
Versão: 2.2 | Atualizado: 11 de Abril de 2026

---

## Visão Geral das Fases

| Fase | Nome | Prioridade | Status |
|------|------|------------|--------|
| **0** | Infraestrutura e Scaffolding | Crítica | ✅ Concluída |
| **1** | MVP — Núcleo de Dinâmica de Voo | Crítica | ✅ Concluída |
| **2** | Módulo do Grupo Motopropulsor | Alta | ✅ Concluída |
| **3** | Módulo de Diagnóstico e Falhas (EICAS) | Alta | ✅ Concluída |
| **4** | Polimento e UX (Menu Superior / Playback) | Média | ✅ Concluída |
| **5** | Redesign Visual e Dashboards Avançados | Média | 🚧 Em Progresso |
| **6** | Alertas Sonoros e Exportação | Baixa | 📋 Planejada |
| **7** | Modo Comparativo e Analytics Avançado | Baixa | 📋 Planejada |
| **8** | Modos de Renderização (Desempenho / Compatibilidade) | Alta | 📋 Planejada — ver `docs/backlog/modos_renderizacao.md` |

---

## FASE 4 — Polimento e UX ✅

**Objetivo:** Otimizar o uso de espaço e a fluidez da análise de dados.
**Status:** Concluída em 10/04/2026

### Entregas
- [x] **Menu Superior Horizontal:** Migração da barra lateral para o topo, economizando 20% de área útil.
- [x] **Controle de Playback:** Implementação de botão Play/Pause sincronizado com o slider de tempo.
- [x] **Histórico Dinâmico:** Seletor de arquivos recentes para troca rápida de contexto de análise.
- [x] **Vertical Alignment:** Padronização das alturas dos boxes de métricas superiores (320px).

---

## FASE 5 — Redesign Visual e Dashboards Avançados 🚧

**Objetivo:** Trazer uma estética de "cockpit" e integrar lógica de alertas avançada.
**Status:** Iniciada em 10/04/2026

### Entregas Realizadas
- [x] **Landing Page Centralizada:** Redesign da página inicial com logo e aeronave em composição simétrica.
- [x] **Fault Panel (Ghosting):** Painel central de alertas que exibe sistemas monitorados mesmo quando inativos (estilo cockpit real).
- [x] **Integração MWC/MW\*:** Lógica dinâmica que traduz bits de falha em mensagens de texto coloridas.
- [x] **Refatoração de Pacotes:** Transformação do diretório `ui_components` em um pacote Python modular.
- [x] **Cabeçalho de Metadados da Aeronave:** Extração e exibição de ID, número de série e outros dados do cabeçalho do CSV.
- [x] **Correção de Menu Duplicado (B-01):** `render_top_menu` unificado em `main()` como instância única.
- [x] **Validação de y_col (B-02):** Fallback seguro ao trocar arquivo via histórico, sem risco de `KeyError`.
- [x] **Cache de alertas.json (S-02):** `_ALERT_DEFS` carregado uma única vez no módulo, eliminando I/O por rerun.
- [x] **Toggle Horizonte Artificial (S-03):** Botão `🌐 Horizonte Artificial` alterna entre `FaultPanel` e `AttitudeIndicator`.
- [x] **Detecção de Cabeçalho Robusta (S-04):** Aceita `TIME` ou `STIME`; extrai hora VADR interna, hora GPS real e calcula desvio de relógio (Δ Clock).
- [x] **Coluna PHASE pré-computada (S-05):** `DataLoader._coerce_types()` gera `PHASE` (ground/flight) e salva no Parquet; `add_phase_bands()` lê diretamente, sem recálculo.
- [x] **Truncagem de alertas no FaultPanel (S-06):** `overflow:hidden; text-overflow:ellipsis` + tooltip `title` com nome completo.
- [x] **Visibilidade de Variáveis Sub-rate:** Inclusão de `connectgaps=True` no gráfico temporal e `PCL` nas `CORE_COLUMNS` (`data_loader.py`) garantindo exibição de variáveis de baixa taxa de atualização sem quebras visuais.

### Próximos Passos
- [ ] **Verificação de Validade de Dados (I-06):** Usar colunas de validade (`BALTV`, `MACHV`, `ITTV`) para sinalizar dados inválidos — planejado para esta fase (ver `IDEIAS.MD`).
- [ ] **Avisos Sonoros (Audio Alerts):** Implementação de Master Caution chime e alertas de voz para falhas críticas.
- [ ] **Exportação de Relatórios:** Geração de PDF com resumo das falhas encontradas no voo.
- [ ] **Modo Comparativo:** Carregamento de dois voos simultâneos para comparação de performance.

---

## 🐛 FALHAS CONHECIDAS E DÉBITOS TÉCNICOS

Esta seção documenta problemas identificados durante a inspeção do código atual (10/04/2026) que requerem correção.

### 🔴 Crítico

| # | Arquivo | Problema | Impacto |
|---|---------|----------|---------|
| B-01 | `app.py` | ~~`render_top_menu()` chamado dentro de `render_main()`, duplicando o menu.~~ | ✅ **Corrigido em 10/04/2026** — menu movido para `main()` como única instância. |
| B-02 | `app.py` | ~~`y_col` lido do session_state sem validar se a coluna existe no DataFrame atual.~~ | ✅ **Corrigido em 10/04/2026** — fallback validado contra `get_numeric_columns()`. |

### 🟡 Médio

| # | Arquivo | Problema | Impacto |
|---|---------|----------|---------|
| B-03 | `ui_components/__init__.py` | ~~`alertas.json` aberto com `open()` a cada rerun do Streamlit, sem cache.~~ | ✅ **Corrigido (S-02)** — `_ALERT_DEFS` como variável de módulo. |
| B-04 | `ui_components/__init__.py` | ~~Horizonte artificial comentado sem rota alternativa de ativação.~~ | ✅ **Corrigido (S-03)** — toggle `🌐 Horizonte Artificial` ativo. |
| B-05 | `data_loader.py` | ~~Detecção de cabeçalho exigia `"TIME"` e `"Rec"` simultaneamente.~~ | ✅ **Corrigido (S-04)** — aceita `TIME` ou `STIME`; extrai timestamps VADR e GPS. |
| B-06 | `plots.py` | ~~`add_phase_bands()` recalculava WOW a cada rerun para gerar as faixas de fase.~~ | ✅ **Corrigido (S-05)** — coluna `PHASE` pré-computada na ingestão e salva no Parquet. |
| B-10 | `plots.py` | ~~Variáveis constantes/sub-rate (ex: `PCL` = -5.1°) eram omitidas visualmente devido a buracos (NaN) nos dados.~~ | ✅ **Corrigido em 12/04/2026** — Solucionado habilitando `connectgaps=True` e inserindo PCL no `ffill`. |

### 🟢 Menor

| # | Arquivo | Problema | Impacto |
|---|---------|----------|---------|
| B-07 | `ui_components/__init__.py` | ~~`MWC_TRANSLATION` tem apenas 5 entradas mapeadas. Códigos desconhecidos geram mensagem genérica.~~ | ✅ **Verificado em 01/09/2026** — `MWC_TRANSLATION` agora é carregado dinamicamente de `docs/schemas/mwc_data_catalogo.json` (49 códigos catalogados). |
| B-08 | `data_loader.py` | ~~`"Rec #"` e `"Rec"` no conjunto `excluded` podem não capturar variações com espaço/cerquilha.~~ | ✅ **Verificado em 01/09/2026** — todos os 10 CSVs reais disponíveis em `data/raw/` usam consistentemente `"Rec #"`; conjunto `excluded` já cobre a variante observada. Sem evidência de caso real quebrado. |
| B-09 | `fault_panel.py` | ~~Textos longos de alerta transbordavam o box de 16.66% de largura.~~ | ✅ **Corrigido (S-06)** — `overflow:hidden; text-overflow:ellipsis` + tooltip `title`. |

---

## 💡 SUGESTÕES DE MELHORIA

### ✅ Implementadas em 10/04/2026

| # | Área | Implementação |
|---|------|---------------|
| S-01 | `app.py` | Menu unificado em `main()` — `render_top_menu` removido de `render_main`. |
| S-02 | `ui_components/__init__.py` | `alertas.json` carregado uma única vez como `_ALERT_DEFS` no nível de módulo. |
| S-03 | `ui_components/__init__.py` | ~~Toggle `🌐 Horizonte Artificial` alterna entre `FaultPanel` e `AttitudeIndicator`.~~ | ✅ **Reativada em 01/09/2026** — toggle `🌐 Horizonte Artificial` de volta no painel central (RF02); o painel de alertas EICAS (RF06) segue como padrão. |
| S-04 | `data_loader.py` | Detecção de cabeçalho aceita `TIME` ou `STIME`. Extrai `VADR_HOURS/MIN/SEC/DAY/MONTH/YEAR` e `GMT_HOUR/MIN/SEC` para exibir hora de início, hora GPS real e desvio `Δ Clock` no cabeçalho. |
| S-05 | `data_loader.py` + `plots.py` | Coluna `PHASE` (ground/flight) pré-computada em `_coerce_types()` e salva no Parquet. `add_phase_bands()` lê diretamente. |
| S-06 | `fault_panel.py` | Células de alerta com `overflow:hidden; text-overflow:ellipsis` e tooltip `title` com nome completo. |

### 📄 Movida para IDEIAS.MD

| # | Área | Descrição |
|---|------|-----------|
| S-07 → I-15 | `AttitudeBox` | Integração do `vsi.py` (`VerticalSpeedIndicator`) para exibir velocidade vertical (ALTR). |

### ✅ Reimplementadas em 01/09/2026 — Fechamento dos requisitos do Modo VADR

Auditoria contra `docs/02_requirements.md` (ver `docs/RETOMADA.md` §13) apontou três requisitos formais que tinham sido descontinuados ao longo das iterações. Todos foram reimplementados:

| RF | Requisito | Implementação |
|----|-----------|---------------|
| **RF02** | Horizonte artificial reagindo a pitch/roll | Toggle `🌐 Horizonte Artificial` no painel central alterna com o `FaultPanel` (S-03 reativada). `AttitudeIndicator` já existia pronto, só estava desconectado da UI. |
| **RF04** | Cards de Subsistemas (Box Inferior) | `SubsystemCards` restaurado do histórico (versão já com `safe_numeric` da auditoria) e reconectado em `views/vadr.py`: Trem de Pouso, Carga Estrutural (NZ), Resumo do Motor e Manete (PCL). |
| **RF05.1** | Play/Pause de reprodução automática | Botão ▶/⏸ em linha própria acima do slider. Avanço calculado para percorrer o voo inteiro em ~60 s a 5 FPS, independente do tamanho do arquivo; para sozinho no último quadro, reinicia se acionado no fim, e mover o slider pausa. O próximo quadro é agendado por `st.fragment(run_every=...)`, que reexecuta apenas o painel de análise. |

Cobertura: `tests/test_time_controller.py` (9 testes) para a lógica de playback, mais validação de integração via `streamlit.testing.v1.AppTest` nos modos VADR e Completa.

### 📅 Futuras (não priorizadas)

| # | Área | Sugestão | Benefício |
|---|------|----------|-----------| 
| S-08 | Geral | Implementar um **modo escuro/claro** opcional na landing page. | Acessibilidade e preferência do usuário. |
| S-09 | `TimeController` | Controle de **velocidade de playback** (0.5x, 1x, 2x, 5x) além do Play/Pause. | Análise de eventos críticos em câmera lenta. |
| S-10 | `EICASPanel` | Expandir `MWC_TRANSLATION` com todos os códigos documentados no manual do motor. | Elimina B-07, melhora o diagnóstico de PMU. |
| S-16 | `ui_components/` | **Bloco de Atitude + Geolocalização:** novo componente dedicado com `AttitudeIndicator` (horizonte artificial, pitch/roll em tempo real) + mapa Google Maps exibindo a trilha GPS do voo (`GPSLAT`/`GPSLONG`) e posição atual do cursor temporal. | Reutiliza `AttitudeIndicator` já implementado (`self._attitude` em `AttitudeBox`). Requer Google Maps JavaScript API ou `streamlit-folium` como alternativa open-source. |

### Fase 6 — Alertas Sonoros e Exportação (Planejada)

- **S-11:** Integrar `st.audio()` com arquivo WAV para Master Caution chime quando um Warning ativo for detectado.
- **S-12:** Gerar relatório PDF (via `reportlab` ou `fpdf2`) com: metadados da aeronave, lista de falhas detectadas, gráfico temporal salvo e estatísticas do voo.
- **S-13:** Adicionar botão de download de CSV filtrado para o intervalo de tempo selecionado.

### Fase 7 — Modo Comparativo (Planejada)

- **S-14:** Suporte a dois DataFrames simultâneos (`df_a`, `df_b`), com o gráfico temporal sobrepondo as duas séries em cores distintas.
- **S-15:** Delta automático entre os dois voos: variáveis com maior divergência são sinalizadas para investigação.

### Fase 8 — Modos de Renderização (Planejada, prioridade alta)

📄 **Plano detalhado:** `docs/backlog/modos_renderizacao.md`

Introduz a escolha **⚡ Desempenho (WebGL)** / **🛡️ Compatibilidade** na landing page, atacando dois problemas levantados em 01/09/2026:

- **Precisão:** a decimação atual usa *stride* uniforme, que **descarta picos estreitos** — exatamente os transientes que importam numa análise de voo. Será substituída por **envelope min/máx por bucket** (a mesma técnica de osciloscópio), compartilhada pelos dois modos.
- **Fluidez:** 60 FPS é inalcançável no modelo server-side (piso de dezenas de ms por quadro). O modo Desempenho migra o viewport para o navegador, onde o gráfico é desenhado uma única vez e só o cursor se move.

| Etapa | Branch | Entrega | Risco |
|-------|--------|---------|-------|
| 1 | `feature/render-modes-etapa1` | Seletor + `Scattergl` + envelope min/máx (sem JavaScript) | Baixo |
| 2 | `feature/viewport-clientside` | Playback 60 FPS, zoom com re-decimação, seguir-cursor | Médio |
| 3 | `feature/instrumentos-svg` | Instrumentos em SVG, tudo sincronizado a 60 FPS | Alto |

> **Decisão de produto registrada:** os modos **não serão equivalentes**. Seguir-cursor e zoom sincronizado existirão só no modo Desempenho — Compatibilidade é fallback degradado, não espelho.

---

## ⚙️ ESTADO DO AMBIENTE TÉCNICO

| Componente | Estado | Versão/Observação |
|------------|--------|-------------------|
| `app.py` | ✅ Funcional | Menu unificado em `main()` — B-01 e B-02 corrigidos |
| `src/data_loader.py` | ✅ Funcional | Cache Parquet ativo; detecção de cabeçalho robusta (S-04/S-05) |
| `src/plots.py` | ✅ Funcional | `add_phase_bands()` lê coluna `PHASE` pré-computada (S-05) |
| `src/ui_components/__init__.py` | ✅ Funcional | Toggle Horizonte Artificial ativo (S-03); cache JSON (S-02) |
| `src/ui_components/fault_panel.py` | ✅ Funcional | Grid ghosting + truncagem com tooltip (S-06) |
| `src/ui_components/vsi.py` | ⚠️ Não integrado | Componente VSI pronto — aguarda I-15 no IDEIAS.MD |
| `src/ui_components/alertas.json` | ✅ Presente | 56 alertas EICAS catalogados; carregado uma vez (S-02) |
| `requirements.txt` | ✅ Presente | Verificar versões congeladas |

> ⚠️ **Atenção:** Parquets gerados antes de 10/04/2026 não possuem a coluna `PHASE`. Recarregue os CSVs ou apague os arquivos em `data/processed/` para forçar a reingestão.

---

## Arquivos de Referência para a Equipe

| Documento | Conteúdo |
|-----------|----------|
| `SCS.md` | Especificação completa de requisitos (RF, UI, RNF) |
| `Dicionario_de_Dados_VADER.md` | Mapeamento de variáveis CSV por fase, classificado por tipo de sinal (v2.0) |
| `variaveis.json` | **Schema de telemetria** — fonte de verdade para tipo de sinal, faixas e resolução de variáveis da aeronave |
| `EICAS.md` | Especificação técnica do sistema EICAS do A-29 |
| `VADR.md` | Especificação técnica do sistema VADR do A-29 |
| `IDEIAS.MD` | Banco de ideias e funcionalidades futuras catalogadas |
| `Guia_UI_EICAS.md` | Guia de interface para o painel de alertas |
| `10ABR.MD` | Detalhamento técnico das mudanças de 10/04/2026 |


