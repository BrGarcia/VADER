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
| DUP-02 (estilos DTC duplicados entre `dtc.py`/`completa.py`) | Confirmado sem divergência entre as duas cópias; continua pendente no `relatorio_plan.md`, não é bug |
| Suspeita descartada: diff/shift cruzando fronteira de `Origem_Arquivo` na concatenação de múltiplos `.DMP` | Mesmo comportamento existe no script de referência original (baseado na macro VBA legada) — parece ser característica assumida do design, não bug |
| `docs/dtc-mode/conversor.py` (script de referência standalone, fora do app) | Ainda tem o mesmo BUG-07 não corrigido — não é chamado pelo Streamlit, então não é urgente, mas fica registrado caso alguém ainda o use manualmente |

**Commit gerado:** `48ea9da` (fix isolado do BUG-07) + commit pendente com o restante (falhas visíveis na UI + arquivamento do TRIMM legado).

---

## 7. Princípio Norteador

Depois de um período parado, **não conte com a memória do estado anterior** — trate o repositório como se fosse herdado de outra pessoa. Verifique antes de assumir: se um arquivo de plano ou roadmap menciona algo como "feito", confirme no código atual antes de construir em cima dele.
