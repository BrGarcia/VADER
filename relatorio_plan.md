# 📋 Plano de Implementação — Itens Pendentes da Auditoria

**Data:** 2026-05-18  
**Branch:** `fix/auditoria-tecnica`  
**Referência:** `relatorio.md` — Seção 7

> ✅ **Plano encerrado em 01/09/2026 (ver `docs/RETOMADA.md`):** todos os itens foram resolvidos — a maioria via merge de `fix/auditoria-tecnica` (que já os tinha implementado numa branch nunca antes mesclada), DUP-02/DUP-03 diretamente nesta branch antes do merge, e IMP-07 marcado obsoleto (recurso que o item propunha otimizar foi removido da UI).

---

## Fase 1 — Infraestrutura (pré-requisitos)

### 1.1 — IMP-01: Framework de Logging — ✅ resolvido (merge 01/09/2026)

**Arquivo a criar:** `src/utils/logger.py`  
**Impacto:** Todos os módulos que usam `print()` para erros  

**Plano:**
1. Criar módulo `logger.py` com `logging.getLogger("vader")` configurado
2. Substituir todos os `print(f"[VADER]...")` e `print(f"Erro...")` por chamadas ao logger
3. Arquivos afetados: `components/__init__.py`, `dtc_parser.py`, `trimm_converter.py` (archive), `video_converter.py`

### 1.2 — DUP-01: Função `_safe()` centralizada — ✅ resolvido (merge 01/09/2026)

**Arquivo a criar:** `src/utils/helpers.py`  
**Impacto:** `components/__init__.py` (3 ocorrências), `plots.py` (1 ocorrência)

**Plano:**
1. Criar `safe_numeric()` em `src/utils/helpers.py`
2. Importar e substituir as 4 closures `_safe()` locais
3. Manter a assinatura compatível: `safe_numeric(source, key, fallback=0.0) -> float`

---

## Fase 2 — Eliminação de Duplicações

### 2.1 — DUP-02: Estilos DTC centralizados — ✅ resolvido em 01/09/2026

**Arquivo a criar:** `src/ui/components/dtc_styles.py`  
**Impacto:** `views/dtc.py`, `views/completa.py`

**Plano:**
1. Extrair `highlight_status_t()`, `highlight_test_1()` e `aplicar_estilos()` para módulo dedicado
2. A função `aplicar_estilos(df)` recebe o DataFrame e retorna o Styler pronto
3. Remover definições duplicadas de ambas as views

### 2.2 — DUP-03: Painel de vídeo unificado — ✅ resolvido (merge 01/09/2026)

**Arquivo afetado:** `views/completa.py`  

**Plano:**
1. Criar função `_render_video_panel(title, videos, rotate, key_prefix)` dentro de `completa.py`
2. Substituir os blocos EICAS (linhas 24-65) e CHVC (linhas 67-108) por chamadas à função
3. Diferenças parametrizadas: `title`, `rotate`, `key_prefix`

### 2.3 — DUP-04: Cor de motor unificada — ✅ resolvido (merge 01/09/2026)

**Arquivo afetado:** `components/__init__.py`, `plots.py`  

**Plano:**
1. A função canônica já existe em `plots.py` como `EngineGaugePlotter._get_color()`
2. Extrair para função de módulo `get_engine_color(value, variable)` em `plots.py`
3. Importar em `components/__init__.py` e remover `_get_engine_color()` local

> **Resolvido via merge:** `get_engine_color()` unificado em `plots.py`, importado por `components/__init__.py`. A divergência de cor "normal" (branco vs. verde fixo) foi resolvida a favor de `COLORS["normal"]` (branco) — mudança visual pequena no card de resumo do motor, aceita como parte da consolidação.

---

## Fase 3 — Correções Menores

### 3.1 — BUG-08: Roteador não define `modo_app` para VADR — ✅ resolvido em 01/09/2026

**Arquivo:** `app.py`  
**Plano:** Setar `st.session_state.modo_app = "vadr"` no bloco elif do VADR

> Corrigido: `landing.py` agora seta `modo_app = "vadr"` nos dois pontos de ingestão, e `app.py` checa `modo == "vadr"` explicitamente em vez de inferir por exclusão (`modo != "completa"`).

### 3.2 — DEAD-05: AttitudeIndicator como TODO — ✅ já estava resolvido

**Arquivo:** `components/__init__.py`  
**Plano:** Adicionar comentário `# TODO` documentando uso futuro

> Verificado: comentário já existe (`components/__init__.py:260`) documentando que `self._attitude` está preservado para uso futuro.

### 3.3 — IMP-07: FlightMap instanciado como constante de módulo — ⏸ obsoleto

**Arquivo:** `views/vadr.py`  
**Plano:** Mover instanciação para nível de módulo `_FLIGHT_MAP = FlightMap()`

> **Achado (01/09/2026):** `FlightMap` (`src/ui/components/flight_map.py`) não é mais importado em lugar nenhum do código — o recurso de mapa foi removido da UI num commit posterior a este plano. O item ficou obsoleto; a ação recomendada agora é decidir entre remover o arquivo morto ou mantê-lo como base para reativação futura (ver ROADMAP S-16).

---

## Fase 4 — Melhorias de Arquitetura (IMP-03..09)

### 4.1 — IMP-09: Validação de estrutura CSV — ✅ resolvido (merge 01/09/2026)

**Arquivo:** `data_loader.py`  
**Plano:** Adicionar checagem de colunas TIME/STIME após leitura

### 4.2 — IMP-05: Imports no topo dos módulos — ✅ resolvido (merge 01/09/2026)

**Arquivos:** `landing.py`, `completa.py`  
**Plano:** Mover imports de `DtcParser`, `video_converter`, `local_scanner` para o topo

### 4.3 — IMP-02: Estrutura de testes (skeleton) — ✅ resolvido (merge 01/09/2026)

**Diretório a criar:** `tests/`  
**Plano:** Criar skeleton com `conftest.py` e um teste básico para `data_loader` e `dtc_parser`

---

## Ordem de Execução

1. IMP-01 (logger) → base para os demais
2. DUP-01 (helpers.py) → desbloqueia refatorações
3. DUP-04 (cor motor) → simples, uma função
4. DUP-02 (estilos DTC) → novo arquivo
5. DUP-03 (vídeo panel) → refatoração interna
6. BUG-08 + DEAD-05 + IMP-07 → correções pontuais
7. IMP-09 + IMP-05 → melhorias de robustez
8. IMP-02 (testes skeleton)
