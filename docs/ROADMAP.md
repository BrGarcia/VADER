# ROADMAP — V.A.D.E.R.
**Visualizador Analítico de Dados de Engenharia e Rastreio**
Versão: 2.1 | Atualizado: 10 de Abril de 2026

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

### 🟢 Menor

| # | Arquivo | Problema | Impacto |
|---|---------|----------|---------|
| B-07 | `ui_components/__init__.py` | `MWC_TRANSLATION` tem apenas 5 entradas mapeadas. Códigos desconhecidos geram mensagem genérica. | Usuário não consegue interpretar alertas PMU não mapeados. |
| B-08 | `data_loader.py` | `"Rec #"` e `"Rec"` no conjunto `excluded` podem não capturar variações com espaço/cerquilha. | Inconsistência na filtragem de colunas. |
| B-09 | `fault_panel.py` | ~~Textos longos de alerta transbordavam o box de 16.66% de largura.~~ | ✅ **Corrigido (S-06)** — `overflow:hidden; text-overflow:ellipsis` + tooltip `title`. |

---

## 💡 SUGESTÕES DE MELHORIA

### ✅ Implementadas em 10/04/2026

| # | Área | Implementação |
|---|------|---------------|
| S-01 | `app.py` | Menu unificado em `main()` — `render_top_menu` removido de `render_main`. |
| S-02 | `ui_components/__init__.py` | `alertas.json` carregado uma única vez como `_ALERT_DEFS` no nível de módulo. |
| S-03 | `ui_components/__init__.py` | Toggle `🌐 Horizonte Artificial` alterna entre `FaultPanel` e `AttitudeIndicator`. |
| S-04 | `data_loader.py` | Detecção de cabeçalho aceita `TIME` ou `STIME`. Extrai `VADR_HOURS/MIN/SEC/DAY/MONTH/YEAR` e `GMT_HOUR/MIN/SEC` para exibir hora de início, hora GPS real e desvio `Δ Clock` no cabeçalho. |
| S-05 | `data_loader.py` + `plots.py` | Coluna `PHASE` (ground/flight) pré-computada em `_coerce_types()` e salva no Parquet. `add_phase_bands()` lê diretamente. |
| S-06 | `fault_panel.py` | Células de alerta com `overflow:hidden; text-overflow:ellipsis` e tooltip `title` com nome completo. |

### 📄 Movida para IDEIAS.MD

| # | Área | Descrição |
|---|------|-----------|
| S-07 → I-15 | `AttitudeBox` | Integração do `vsi.py` (`VerticalSpeedIndicator`) para exibir velocidade vertical (ALTR). |

### 📅 Futuras (não priorizadas)

| # | Área | Sugestão | Benefício |
|---|------|----------|-----------| 
| S-08 | Geral | Implementar um **modo escuro/claro** opcional na landing page. | Acessibilidade e preferência do usuário. |
| S-09 | `TimeController` | Controle de **velocidade de playback** (0.5x, 1x, 2x, 5x) além do Play/Pause. | Análise de eventos críticos em câmera lenta. |
| S-10 | `EICASPanel` | Expandir `MWC_TRANSLATION` com todos os códigos documentados no manual do motor. | Elimina B-07, melhora o diagnóstico de PMU. |

### Fase 6 — Alertas Sonoros e Exportação (Planejada)

- **S-11:** Integrar `st.audio()` com arquivo WAV para Master Caution chime quando um Warning ativo for detectado.
- **S-12:** Gerar relatório PDF (via `reportlab` ou `fpdf2`) com: metadados da aeronave, lista de falhas detectadas, gráfico temporal salvo e estatísticas do voo.
- **S-13:** Adicionar botão de download de CSV filtrado para o intervalo de tempo selecionado.

### Fase 7 — Modo Comparativo (Planejada)

- **S-14:** Suporte a dois DataFrames simultâneos (`df_a`, `df_b`), com o gráfico temporal sobrepondo as duas séries em cores distintas.
- **S-15:** Delta automático entre os dois voos: variáveis com maior divergência são sinalizadas para investigação.

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
| `Dicionario_de_Dados_VADER.md` | Mapeamento de variáveis CSV por fase |
| `EICAS.md` | Especificação técnica do sistema EICAS do A-29 |
| `VADR.md` | Especificação técnica do sistema VADR do A-29 |
| `IDEIAS.MD` | Banco de ideias e funcionalidades futuras catalogadas |
| `Guia_UI_EICAS.md` | Guia de interface para o painel de alertas |
| `10ABR.MD` | Detalhamento técnico das mudanças de 10/04/2026 |


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
- [x] **Integração MWC/MW*:** Lógica dinâmica que traduz bits de falha em mensagens de texto coloridas.
- [x] **Refatoração de Pacotes:** Transformação do diretório `ui_components` em um pacote Python modular.
- [x] **Cabeçalho de Metadados da Aeronave:** Extração e exibição de ID, número de série e outros dados do cabeçalho do CSV.

### Próximos Passos
- [ ] **Horizonte Artificial (Restauração):** Reativar o `AttitudeIndicator` com um botão de alternância para o painel de alertas.
- [ ] **Avisos Sonoros (Audio Alerts):** Implementação de Master Caution chime e alertas de voz para falhas críticas (ex: "FIRE", "OIL PRESSURE").
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
| B-03 | `ui_components/__init__.py` (L231-236) | O arquivo `alertas.json` é aberto com `open()` dentro de um método de renderização executado a cada rerun do Streamlit, sem cache. | I/O desnecessário e latência em cada atualização de frame. |
| B-04 | `ui_components/__init__.py` (L227-228) | O horizonte artificial (`AttitudeIndicator`) está comentado sem uma rota alternativa de ativação. | Feature completa de Fase 1/2 inacessível sem editar o código. |
| B-05 | `data_loader.py` (L86-88) | A detecção da linha de cabeçalho procura por `"TIME"` e `"Rec"`, mas CSVs com formatos ligeiramente diferentes (ex.: `"STIME"` sem `"Rec"`) podem retornar o fallback `8` incorretamente. | Falha silenciosa na leitura de dados para arquivos não-padrão. |
| B-06 | `plots.py` (L203-207) | Em `add_phase_bands()`, o `groupby(run_id)` itera sobre cada segmento de fase de voo. Em voos longos com muitas transições WOW, isso pode ser lento. | Performance degradada com muitos eventos de pouso/decolagem. |

### 🟢 Menor

| # | Arquivo | Problema | Impacto |
|---|---------|----------|---------|
| B-07 | `ui_components/__init__.py` (L24-30) | `MWC_TRANSLATION` tem apenas 5 entradas mapeadas. Códigos desconhecidos geram `"MWC CODE {n}"` genérico sem descrição útil. | Usuário não consegue interpretar alertas PMU não mapeados. |
| B-08 | `data_loader.py` (L195-196) | `"Rec #"` e `"Rec"` estão no conjunto `excluded`, mas não há tratamento para a coluna `"Rec #"` com o espaço e cerquilha (pode quebrar em alguns parsers). | Inconsistência na filtragem de colunas. |
| B-09 | `fault_panel.py` | Textos longos de alerta (ex: `"ENG MAN - PMU FAIL"`) transbordam o box de 16.66% de largura. | Alertas com descrição longa ficam ilegíveis no grid. |

---

## 💡 SUGESTÕES DE MELHORIA

### Arquitetura e Código

| # | Área | Sugestão | Benefício |
|---|------|----------|-----------|
| S-01 | `app.py` | Refatorar o menu de configurações para um componente `SettingsPanel` separado, eliminar a chamada duplicada em `render_main()`. | Elimina B-01, simplifica o fluxo de dados principal. |
| S-02 | `ui_components/__init__.py` | Cachear o carregamento do `alertas.json` com `@st.cache_data` ou como variável de módulo. | Elimina B-03, reduz I/O em até 20x. |
| S-03 | `ui_components/__init__.py` | Adicionar botão `st.toggle("Horizonte Artificial")` para alternar entre o `FaultPanel` e o `AttitudeIndicator`. | Restaura feature de Fase 1 sem remoção do painel de alertas. |
| S-04 | `data_loader.py` | Tornar a lógica de detecção de cabeçalho mais robusta: procurar por `"TIME"` **OU** `"STIME"` para cobrir ambos os formatos VADR. Nota do desenvolvedor: o arquivo CSV possui VADR_HOURS,VADR_MINUTES,VADR_SECOND,VADR_DAY,VADR_MONTH,VADR_YEAR (que sao informações de data e hora gravadas na memoria interna do VADR) além GMT_HOUR,GMT_MIN,GMT_SEC (que sao informações precisas e reais de hora, minuto e segundo, fornecidas pelo GPS através da conexao arinc429). fazendo essa leitura desses arquivosé possivel verificar discrepancia entre a hora interna do VADR e a hora real do GPS. podemos usar essa informacao tambem para adicionar no cabeçalho da analise a hora GMT do inicio do voo e a hora GMT do final do voo  | Elimina B-05, compatibilidade com mais versões do VADR. |
| S-05 | `plots.py` | Mover a lógica de `add_phase_bands()` para processamento em `DataLoader._coerce_types()`, salvando a coluna `PHASE` no Parquet. | Elimina B-06, não recalcula o WOW a cada rerun. |

### Experiência do Usuário

| # | Área | Sugestão | Benefício |
|---|------|----------|-----------|
| S-06 | `FaultPanel` | Truncar textos de alerta com `overflow: hidden; text-overflow: ellipsis` e exibir o nome completo em `title` (tooltip nativo HTML). | Elimina B-09, mantém o grid compacto. |
| S-07 | `AttitudeBox` | Adicionar indicador de **velocidade vertical (VSI)** já que o componente `vsi.py` existe no pacote mas não está sendo utilizado. | Ativa componente pronto e adiciona dado relevante. |
| S-08 | Geral | Implementar um **modo escuro/claro** opcional na landing page. | Acessibilidade e preferência do usuário. |
| S-09 | `TimeController` | Adicionar controle de **velocidade de playback** (0.5x, 1x, 2x, 5x) além do Play/Pause. | Análise de eventos críticos em câmera lenta. |
| S-10 | `EICASPanel` | Expandir `MWC_TRANSLATION` com todos os códigos documentados no manual do motor. | Elimina B-07, melhora o diagnóstico de PMU. |

### Fase 6 — Alertas Sonoros e Exportação (Planejada)

- **S-11:** Integrar `st.audio()` com arquivo WAV para Master Caution chime quando um Warning ativo for detectado.
- **S-12:** Gerar relatório PDF (via `reportlab` ou `fpdf2`) com: metadados da aeronave, lista de falhas detectadas, gráfico temporal salvo e estatísticas do voo.
- **S-13:** Adicionar botão de download de CSV filtrado para o intervalo de tempo selecionado.

### Fase 7 — Modo Comparativo (Planejada)

- **S-14:** Suporte a dois DataFrames simultâneos (`df_a`, `df_b`), com o gráfico temporal sobrepondo as duas séries em cores distintas.
- **S-15:** Delta automático entre os dois voos: variáveis com maior divergência são sinalizadas para investigação.

---

## ⚙️ ESTADO DO AMBIENTE TÉCNICO

| Componente | Estado | Versão/Observação |
|------------|--------|-------------------|
| `app.py` | ✅ Funcional | Ponto de entrada Streamlit |
| `src/data_loader.py` | ✅ Funcional | Cache Parquet ativo |
| `src/plots.py` | ✅ Funcional | `AttitudeIndicator` completo mas inativo |
| `src/ui_components/__init__.py` | ✅ Funcional | 4 componentes exportados |
| `src/ui_components/fault_panel.py` | ✅ Funcional | Grid ghosting implementado |
| `src/ui_components/vsi.py` | ⚠️ Não utilizado | Componente VSI pronto mas sem integração |
| `src/ui_components/alertas.json` | ✅ Presente | 56 alertas EICAS catalogados |
| `requirements.txt` | ✅ Presente | Verificar versões congeladas |

---

## Arquivos de Referência para a Equipe

| Documento | Conteúdo |
|-----------|----------|
| `SCS.md` | Especificação completa de requisitos (RF, UI, RNF) |
| `Dicionario_de_Dados_VADER.md` | Mapeamento de variáveis CSV por fase |
| `EICAS.md` | Especificação técnica do sistema EICAS do A-29 |
| `VADR.md` | Especificação técnica do sistema VADR do A-29 |
| `Guia_UI_EICAS.md` | Guia de interface para o painel de alertas |
| `10ABR.MD` | Detalhamento técnico das mudanças de 10/04/2026 |
