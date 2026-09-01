# Estratégia de Retomada do Desenvolvimento

**Data:** 2026-08-31
**Motivação:** O projeto ficou um período sem atenção. Este documento define como reabrir o desenvolvimento com segurança, sem perder trabalho pendente e sem retrabalho sobre uma base cujo estado real não foi verificado.

---

## 1. Diagnóstico do Estado Atual

Levantamento feito em 31/08/2026, na branch `feature/modo-vadr`:

| Item | Situação |
|------|----------|
| Working tree | Mudança pendente não commitada: conversão da timeline de segundos → minutos (`plots.py`, `vadr.py`), consistente em 7 pontos (eixo, hover, cursor, bandas). Parece completa. |
| `docs/CSV/EXEMPLO_CSV.csv` | Deletado no working tree, ainda não confirmado via commit. |
| Arquivos não rastreados | `archive/` (código legado `app_ia.py`/`app_ai.txt`), manuais técnicos ANV (`docs/manuais_anv/*.PDF`), dois schemas novos (`aircraft_telemetry_schema_v1.json`, `variaveis_v1.json`), `relatorio_plan.md`, cópia de relatório. |
| `relatorio_plan.md` | Plano de refatoração de uma auditoria técnica (18/05/2026) — logger centralizado, `helpers.py`, dedup de estilos DTC, testes — **nunca executado**. Nenhum dos artefatos (`src/utils/logger.py`, `tests/`) existe. |
| Testes automatizados | Inexistentes. |
| `requirements.txt` | Versões abertas (`>=`), sem lock — risco de drift silencioso após meses parado. |
| Schemas de variáveis | `variaveis.json` e `variaveis_v1.json` coexistem — não está claro qual é a fonte de verdade atual. |
| Débitos conhecidos (ROADMAP) | B-07 (`MWC_TRANSLATION` incompleto), B-08 (variações de nome de coluna `"Rec #"`/`"Rec"`) — menores, ainda abertos. |

**Conclusão do diagnóstico:** o maior risco não é falta de direção (o projeto tem documentação de arquitetura e roadmap maduros), e sim a incerteza sobre o que no working tree é intencional, o que está obsoleto, e se a aplicação ainda roda sem regressão silenciosa.

---

## 2. Estratégia: 3 Fases

### Fase A — Baseline Limpa (pré-requisito, antes de qualquer feature nova)

1. Decidir, item a item, o destino de cada arquivo pendente do `git status`:
   - Commitar a conversão segundos→minutos (parece pronta).
   - Confirmar a remoção de `EXEMPLO_CSV.csv` (ou restaurar, se ainda referenciado em docs).
   - Decidir sobre `archive/`: manter versionado como referência histórica, ou remover do repo se for lixo de experimento.
   - Adicionar manuais ANV e schemas ao versionamento (são referência técnica, fazem sentido no repo).
2. Rodar `streamlit run app.py` com um CSV/Parquet de exemplo e validar os 4 modos (`landing`, `vadr`, `dtc`, `completa`) — confirmar que nada quebrou durante o período parado.
3. Só depois disso, considerar o estado do projeto "conhecido" e seguro para novas mudanças.

### Fase B — Triagem do Débito Existente

Antes de abrir trabalho novo, decidir explicitamente o que fazer com o que já está documentado mas não feito:

- **`relatorio_plan.md`**: revisar se ainda é relevante à luz do trabalho mais recente (TRIMM/DTC). Se sim, retomar pela ordem já definida nele (logger → helpers → dedup → correções pontuais → testes). Se não, arquivar/descartar explicitamente em vez de deixar arquivo órfão.
- **ROADMAP B-07/B-08**: itens pequenos, bons candidatos a "quick wins" para reganhar tração antes de features maiores.
- **Consolidar `variaveis.json` vs `variaveis_v1.json`**: definir qual é a fonte de verdade e remover a duplicidade.

### Fase C — Escolher Uma Frente Ativa

Depois das Fases A e B, evitar dispersão: escolher **uma** frente por ciclo, não várias em paralelo. Candidatas observadas no histórico recente (últimos commits, docs/TRIMM_IMPLEMENTATION.md, dtc_parser.py):

1. Continuidade do fluxo **TRIMM/DTC** (parece ser a frente mais ativa nos últimos commits).
2. Retomada do **plano de refatoração** (`relatorio_plan.md`), se ainda válido.
3. Itens de **Fase 6/7 do ROADMAP** (alertas sonoros, exportação PDF, modo comparativo) — apenas se A e B estiverem concluídas.

---

## 3. Checklist de Retomada (ordem de execução)

- [x] Resolver `git status` (commit/descartar cada item pendente e não rastreado)
- [x] Smoke test dos 4 modos da aplicação *(parcial — ver nota)*
- [x] Revisar `relatorio_plan.md`: manter, atualizar ou descartar
- [x] Consolidar schemas de variáveis duplicados *(apontado; reconciliação total ainda pendente)*
- [x] Fechar B-07 e B-08 (débitos menores do ROADMAP)
- [ ] Escolher e declarar a frente ativa do próximo ciclo

---

## 5. Fase A — Resultado (01/09/2026)

- **Achado crítico:** dois CSVs de telemetria real ("Mishap Time History Data Set") estavam versionados em `docs/CSV/`, fora da proteção de sigilo que já cobre `/data/`. Removidos do HEAD (`git rm --cached`) e `docs/CSV/*.csv` adicionado ao `.gitignore`. **O histórico do git ainda contém esses arquivos** — purga completa (`git filter-repo`/BFG) é uma decisão separada, ainda em aberto.
- Working tree já estava limpo (commit `4dcc857`, feito fora desta sessão, consolidou tudo que estava pendente na Fase A).
- Smoke test: app sobe sem erro (`streamlit run app.py`, HTTP 200, sem traceback no log) com as dependências do `venv/` (Streamlit 1.50, pandas 2.3.3, plotly 5.24.1, pyarrow 17.0 — todas compatíveis com `requirements.txt`). **Não foi possível validar visualmente os 4 modos** (extensão Claude-in-Chrome não conectada nesta máquina) — só a inicialização do servidor foi confirmada.

## 6. Fase B — Resultado (01/09/2026)

Triagem item a item do débito conhecido, comparando o que os documentos afirmam contra o estado real do código:

| Item | Situação encontrada | Ação tomada |
|------|---------------------|-------------|
| ROADMAP B-07 (`MWC_TRANSLATION` incompleto) | Já resolvido — hoje carrega dinamicamente de `docs/schemas/mwc_data_catalogo.json` (49 códigos) | Marcado ✅ no ROADMAP |
| ROADMAP B-08 (variação `"Rec #"`/`"Rec"`) | Não reproduzido — os 10 CSVs reais em `data/raw/` usam consistentemente `"Rec #"`, já coberto pelo `excluded` | Marcado ✅ no ROADMAP como verificado |
| `relatorio_plan.md` BUG-08 (roteador não seta `modo_app` para VADR) | Confirmado — rota dependia de exclusão implícita (`modo != "completa"`) | **Corrigido**: `landing.py` seta `modo_app = "vadr"`; `app.py` checa `modo == "vadr"` explicitamente |
| `relatorio_plan.md` DEAD-05 (TODO do AttitudeIndicator) | Já resolvido — comentário já existe em `components/__init__.py:260` | Marcado ✅ |
| `relatorio_plan.md` IMP-07 (FlightMap como constante de módulo) | **Obsoleto** — `FlightMap` não é mais importado em nenhum lugar do código (recurso de mapa removido da UI após este plano ser escrito) | Marcado ⏸ obsoleto; **decidido manter** `flight_map.py` como está, para reativação quando o projeto estiver mais robusto (ROADMAP S-16) |
| `relatorio_plan.md` DUP-04 (cor de motor duplicada) | Confirmado duplicado — **e divergente**: `plots.py` usa branco (`COLORS["normal"]`) para estado normal, `components/__init__.py` usa verde fixo (`#00FF88`) | Documentado no plano; não unificado (pode ser intencional, requer confirmação antes de mexer) |
| `relatorio_plan.md` — demais itens (IMP-01 logger, DUP-01 `_safe`, DUP-02 estilos DTC, DUP-03 painel de vídeo, IMP-09 validação CSV, IMP-05 imports, IMP-02 testes) | Nenhum foi implementado | Mantidos como pendentes, plano ainda válido |
| Schemas `variaveis.json` vs `variaveis_v1.json` | **Divergência real**: o código (`src/ui/plots.py`) usa `variaveis_v1.json`, mas `docs/04_data_model.md` e `ROADMAP.md` ainda apontam `variaveis.json` como fonte de verdade. Os dois arquivos têm cobertura de variáveis diferente (ex.: `AS+` vs `AS`) | Aviso adicionado no topo de `docs/04_data_model.md`; **reconciliação completa do índice de variáveis não foi feita** — é uma decisão de conteúdo, não uma correção mecânica |
| `docs/DTC_CONVERSOR_DMP.md` (arquivo novo, não rastreado) | Documentação criada para orientar o entendimento do conversor DTC/DMP | Versionado como está, sem alteração de conteúdo |

**Commits gerados na Fase B:**
- `2b696db` — fix do roteamento VADR (`modo_app`) + toda a documentação de triagem acima
- `d04d463` — `docs/DTC_CONVERSOR_DMP.md`

> Ambos locais na branch `feature/modo-vadr`, ainda **não enviados** para `origin`.

## 8. Fase C — Frente escolhida: revisão do fluxo TRIMM/DTC (01/09/2026)

**Achado prévio à revisão:** `feature/modo-vadr` diverge de `af47022` (8 commits atrás) junto com uma segunda linha independente — `fix/auditoria-tecnica` → `development` → `feature/correcao-fluidez-grafico-temporal` — que já implementou os 28 itens do relatorio de auditoria daquela linha (equivalente ao nosso `relatorio_plan.md`, nunca executado aqui) e inclui uma correção pontual em `dtc_parser.py` (BUG-07). As duas linhas nunca foram mescladas entre si. Decisão tomada: trazer só o fix pontual do DTC para cá, sem reconciliar as branches por inteiro (fica em aberto).

**Revisão do fluxo TRIMM/DTC:**

| Achado | Ação |
|---|---|
| BUG-07 — threshold de detecção calculado só com as 2 primeiras amostras UTC (frágil a outlier pontual) | **Corrigido** (`48ea9da`) — portado isoladamente de `fix/auditoria-tecnica`, sem trazer o resto daquela auditoria |
| `trimm_converter.py`/`trimm_analysis.py` não são importados em lugar nenhum do código; `TRIMM_IMPLEMENTATION.md` já os descrevia como fase exploratória superada pelo `DtcParser` | **Arquivados** em `archive/` — mesma conclusão independente da outra branch (lá catalogado como DEAD-02/DEAD-03) |
| Falhas ao ler um `.DMP` eram engolidas com só um `print()` no console — o operador na UI nunca via o aviso, risco de falso negativo numa ferramenta de detecção de segurança | **Corrigido** — `DtcParser` agora propaga a lista de arquivos que falharam via `metadata["Falhas"]`, e `views/dtc.py`/`views/completa.py` mostram `st.warning()` |
| DUP-02 (estilos DTC duplicados entre `dtc.py`/`completa.py`) | **Corrigido** — extraído para `src/ui/components/dtc_styles.py` (`aplicar_estilos`, `highlight_status_t`, `highlight_test_1`), importado pelas duas views |
| Suspeita descartada: diff/shift cruzando fronteira de `Origem_Arquivo` na concatenação de múltiplos `.DMP` | Mesmo comportamento existe no script de referência original (baseado na macro VBA legada) — parece ser característica assumida do design, não bug |
| `docs/dtc-mode/conversor.py` (script de referência standalone, fora do app) | **Arquivado** em `archive/dtc-mode/conversor.py` — ainda tem o mesmo BUG-07 não corrigido, registrado caso alguém ainda o use manualmente |

## 9. Merge da auditoria técnica (01/09/2026) — `55faa64`

Testado por dry-run que a auditoria completa (`fix/auditoria-tecnica`) é separável do trabalho de fluidez de gráfico (`development`/`feature/correcao-fluidez-grafico-temporal`) — confirmado, mergeada só a primeira. 9 arquivos em conflito, todos do tipo "os dois lados corrigiram o mesmo problema de forma diferente", resolvidos preservando a intenção de ambos os lados quando possível.

**Correção a um achado anterior:** `relatorio_plan.md` não são dois documentos diferentes como eu tinha registrado na Fase C — é o **mesmo documento original** (mesma data, mesmo título) nas duas branches; a versão daqui só tinha as anotações de status que fui adicionando durante a retomada. Resolvido mantendo a versão anotada.

**Itens do `relatorio_plan.md` fechados por este merge** (nenhum exigiu trabalho extra, vieram prontos da outra branch):
- IMP-01 (logger centralizado, `src/utils/logger.py`)
- DUP-01 (`safe_numeric` centralizado, `src/utils/helpers.py`)
- DUP-04 (`get_engine_color` unificado em `plots.py` — a cor "normal" foi padronizada para `COLORS["normal"]` (branco); antes divergia do verde fixo usado no card de resumo do motor — mudança visual pequena, aceita como parte da consolidação)
- IMP-02 (skeleton de testes, `tests/` — 11 testes passando)
- Bônus fora do plano original: BUG-04 em `plots.py` (hover de falha usava `y_column`, que pode ser lista, em vez de `y_ref`), SEC-01 em `vadr.py` (sanitização XSS do nome de arquivo exibido), BUG-01/BUG-02 em `flight_map.py` (except genérico e reatribuição indevida de `snapshot`), `vsi.py` arquivado (nunca integrado)

**Decisões de produto preservadas durante o merge** (a outra branch tinha essas UIs ativas, mas foram removidas deliberadamente aqui antes da divergência das branches):
- `SubsystemCards` — não reintroduzido em `components/__init__.py`/`vadr.py`
- Mapa de Rastreio Geográfico (`FlightMap.render`) — não reintroduzido em `vadr.py`; `flight_map.py` continua arquivado/inativo por decisão explícita, só recebeu os bug fixes de qualquer forma (não afeta nada em execução)

**Conferido depois:** IMP-09 (validação de estrutura CSV, `data_loader.py:160`) e IMP-05 (imports movidos para o topo em `landing.py`/`completa.py`) também vieram prontos no merge. Com isso, **todo o `relatorio_plan.md` está fechado** — DUP-02/DUP-03 já tinham sido resolvidos nesta branch antes do merge, o resto veio de `fix/auditoria-tecnica`.

`requirements.txt` ganhou faixas de versão (`<major seguinte>`) e `pytest`/`pydeck`/`numpy` explícitos; `openpyxl` removido (não usado em nenhum código ativo, só no `conversor.py` arquivado).

Smoke test: `streamlit run app.py` sobe sem traceback (HTTP 200); `pytest tests/` — 11 passed. **Validação visual na UI não foi possível** — a extensão Claude-in-Chrome não conectou nesta sessão apesar de o usuário ter configurado a conexão.

**Commit gerado:** `48ea9da` (fix isolado do BUG-07) + commit pendente com o restante (falhas visíveis na UI + arquivamento do TRIMM legado).

## 10. Merge da fluidez do gráfico (01/09/2026) — `dbe7180`

Trazido `feature/correcao-fluidez-grafico-temporal` (que já incluía `fix/auditoria-tecnica` + `development` por baixo) em cima do merge da auditoria. 3 blocos de conflito, todos em `plots.py`, resolvidos combinando a decimação/normalização da outra branch com a conversão de eixo para minutos desta.

**O que veio:**
- **A.2** — decimação de séries temporais (`_downsample_frame`, stride uniforme, máx. 6000 pontos) — evita recálculo pesado em voos longos.
- **A.3/A.4** — figura base cacheada via `st.cache_data` (`build_base_figure` em `vadr.py`) + `copy.deepcopy` para isolar o cursor temporal do cache.
- **A.5** — normaliza os marcadores de falha para a mesma escala 5–95 das séries principais. Antes, os marcadores usavam o valor real bruto, desalinhado visualmente da curva normalizada — bug real de exibição, corrigido; o valor real fica preservado via `customdata` para o hover.
- **A.6** — modo de análise Básica (28 variáveis) vs. Completa (todas), selecionável na landing page, propagado até `DataLoader.ingest()`. Testado com um CSV real nos dois modos (`basic`: 30 colunas, `complete`: 260 colunas) — sem exceção.
- **SEC-02** — sanitiza filename de upload contra path traversal (`landing.py`).
- `st.plotly_chart` passa a usar `width="stretch"` em vez de `use_container_width` (API mais recente do Streamlit).

**Nota de correção:** a nota anterior desta seção dizia que o próximo passo da metodologia era "aguardando decisão do usuário" — o usuário já decidiu trazer a fluidez agora, então esse passo foi executado nesta mesma sessão, antes de qualquer rename/push de branch.

**Engano de processo corrigido:** o merge foi commitado por engano num branch de teste descartável (`_teste_merge_fluidez`) em vez de `feature/modo-vadr` diretamente. Corrigido com `git branch -f feature/modo-vadr _teste_merge_fluidez` — o conteúdo do commit está correto, só a branch estava errada momentaneamente; nada foi perdido.

Smoke test: compila tudo, `pytest tests/` — 11 passed, `streamlit run app.py` sobe sem traceback (HTTP 200), e testei diretamente via Python (sem UI) `build_base_figure`/`TimelinePlotter.plot`/`add_fault_markers`/`add_phase_bands` e `DataLoader.ingest()` nos dois modos, com um CSV real — sem exceções.

**Validação visual manual (01/09/2026):** usuário rodou o app localmente (landing, VADR nos dois modos de análise, DTC, Completa) e confirmou que está tudo ok — sem regressões visuais, mapa/subsystem cards de fato ausentes conforme esperado.

**Estado da branch agora:** `feature/modo-vadr` tem a auditoria técnica completa + a fluidez do gráfico, tudo local, 15 commits à frente de `origin/feature/modo-vadr`, nada enviado ainda. Próximo passo da metodologia main+development (promover esta branch, sincronizar `main`, limpar branches antigas) segue pendente de decisão do usuário.

## 11. `development` também tinha divergido — merge extra (01/09/2026) — `f24b959`

Ao tentar promover `feature/modo-vadr` a `development`, descoberto que `origin/development` **não era mais ancestral** — seguiu evoluindo sozinha (11 commits) depois que `feature/correcao-fluidez-grafico-temporal` foi cortada dela. Um push normal teria sido rejeitado; forçar teria destruído esse trabalho. Trazido também antes de prosseguir.

**O que veio (trabalho real, não apenas variações cosméticas):**
- Filtro de destaque de excedência (exceedance highlight) no gráfico temporal — feature nova, com seletor de variável/operador/valor limite na UI.
- Variável `FR` (Fuel Remaining) no forward-fill e na análise básica.
- `BASIC_ANALYSIS_COLUMNS` explícita para o modo básico; modo completo expõe todas as colunas sem filtro de validade.
- Gráfico mais alto (+30%), `ticksuffix=" min"`.
- `@st.fragment` em `render_main` — reruns parciais, mais fluido.

**7 conflitos, quase todos cosméticos** (`/60` vs `/60.0`). Um exigiu atenção real: o auto-merge tinha **revertido silenciosamente** `st.plotly_chart` de volta para `use_container_width=True` (API antiga) sem marcar conflito — peguei isso conferindo linha a linha, não veio com marcador `<<<<<<<`. Restaurado `width="stretch"`, já validado funcionando.

Smoke test: compila, `pytest` 11 passed, `streamlit run` sem traceback, e testei via Python o pipeline completo incluindo o novo `exceedance_config` — sem exceções.

## 12. Promoção de branches e sincronização (01/09/2026)

Com `development`, `fix/auditoria-tecnica`, `feature/correcao-fluidez-grafico-temporal` e `main` todas confirmadas como ancestrais de `feature/modo-vadr` (`f24b959`), executado o fechamento da metodologia — tudo via **fast-forward puro, sem force-push**:

1. `git push origin feature/modo-vadr` — `bb678c7..f24b959`
2. `git push origin feature/modo-vadr:development` — `fc51123..f24b959`
3. `git push origin feature/modo-vadr:main` — `af47022..f24b959`
4. Limpeza: `fix/auditoria-tecnica` e `feature/correcao-fluidez-grafico-temporal` já tinham sido apagadas no GitHub (provavelmente automático ao fechar PR) — só restava podar as referências locais obsoletas (`git fetch --prune` + `git branch -d`).

**Estado final:** `main`, `development` e `feature/modo-vadr` apontam todos para o mesmo commit (`f24b959`), sincronizados com seus remotos. A partir daqui, o fluxo esperado é: features novas em branches próprias a partir de `development`, merge de volta, e `main` atualizada em pontos de release — não mais um branch de feature acumulando meses de trabalho como trunk de fato.

---

## 13. Fechamento dos requisitos do Modo VADR (01/09/2026)

Auditoria do Modo VADR contra a spec formal (`docs/02_requirements.md`) encontrou **três requisitos não atendidos** — todos por decisões deliberadas de simplificação tomadas ao longo das iterações, não por bugs:

| RF | Situação encontrada | Ação |
|----|---------------------|------|
| **RF02** — horizonte artificial reagindo a pitch/roll | Só numérico; `AttitudeIndicator` existia completo mas desconectado da UI (S-03 "suspensa") | **Implementado** — toggle `🌐 Horizonte Artificial` alterna com o painel de alertas. O `FaultPanel` (RF06) segue como padrão, então nenhum dos dois requisitos foi sacrificado. |
| **RF04** — Cards de Subsistemas | Ausente; classe removida em commit de simplificação e não reintroduzida nos merges de hoje (decisão consciente na época) | **Implementado** — `SubsystemCards` restaurado do commit `bfad9fa` (versão já refatorada com `safe_numeric`) e religado em `views/vadr.py`. |
| **RF05.1** — Play/Pause automático | Ausente; código dizia literalmente "Removida a pedido" | **Implementado** — botão ▶/⏸ ao lado do slider, ~60 s por voo a 10 FPS independentemente do tamanho do arquivo. |

**Detalhes de implementação do playback (RF05.1):**
- Avanço acontece **antes** de instanciar o slider — o Streamlit proíbe alterar o estado de um widget depois que ele foi criado no mesmo run.
- O slider passou a ser controlado exclusivamente via `session_state` (sem `value=`), para que o playback consiga movê-lo sem conflito de estado.
- `st.rerun(scope="fragment")` reexecuta só o painel de análise (`render_main` é `@st.fragment`), reaproveitando a figura base cacheada. **Bug pego em teste:** esse escopo só é válido *durante* um rerun de fragmento e explodia no primeiro clique — resolvido com fallback para `st.rerun()` completo.
- `TimeController.STATE_KEYS` centraliza as chaves de estado temporal, agora limpas ao trocar de voo (antes, um voo mais curto que o anterior deixaria o slider fora da faixa).

**Validação:** `tests/test_time_controller.py` com 9 testes unitários (passo do playback, parada no fim, reinício no fim, pausa ao mover o slider, correção de índice fora da faixa) — suíte total foi de 11 para 20 testes. Integração validada com `streamlit.testing.v1.AppTest` nos modos VADR e Completa, já que a extensão Claude-in-Chrome não conectou nesta sessão.

---

## 7. Princípio Norteador

Depois de um período parado, **não conte com a memória do estado anterior** — trate o repositório como se fosse herdado de outra pessoa. Verifique antes de assumir: se um arquivo de plano ou roadmap menciona algo como "feito", confirme no código atual antes de construir em cima dele.
