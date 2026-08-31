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

- [ ] Resolver `git status` (commit/descartar cada item pendente e não rastreado)
- [ ] Smoke test dos 4 modos da aplicação
- [ ] Revisar `relatorio_plan.md`: manter, atualizar ou descartar
- [ ] Consolidar schemas de variáveis duplicados
- [ ] Fechar B-07 e B-08 (débitos menores do ROADMAP)
- [ ] Escolher e declarar a frente ativa do próximo ciclo

---

## 4. Princípio Norteador

Depois de um período parado, **não conte com a memória do estado anterior** — trate o repositório como se fosse herdado de outra pessoa. Verifique antes de assumir: se um arquivo de plano ou roadmap menciona algo como "feito", confirme no código atual antes de construir em cima dele.
