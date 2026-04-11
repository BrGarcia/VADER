# ROADMAP — V.A.D.E.R.
**Visualizador Analítico de Dados de Engenharia e Rastreio**
Versão: 2.0 | Atualizado: 10 de Abril de 2026

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
| B-01 | `app.py` (L189) | `render_top_menu(df)` é chamado **dentro** de `render_main()`, o que cria uma **segunda instância** do menu no final da página após os subsistemas, duplicando o uploader. | O formulário aparece duas vezes quando dados são carregados. |
| B-02 | `app.py` (L209) | Ao entrar na branch `df_cached is not None`, o `y_col` é lido do `session_state` mas sem validação se a coluna ainda existe no DataFrame atual (pode ocorrer se o arquivo foi trocado via histórico). | Potencial `KeyError` ao trocar de arquivo via histórico. |

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
| S-04 | `data_loader.py` | Tornar a lógica de detecção de cabeçalho mais robusta: procurar por `"TIME"` **OU** `"STIME"` para cobrir ambos os formatos VADR. | Elimina B-05, compatibilidade com mais versões do VADR. |
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
| `Guia_UI_EICAS.md` | Guia de interface para o painel de alertas |
| `10ABR.MD` | Detalhamento técnico das mudanças de 10/04/2026 |
