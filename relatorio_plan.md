# 📋 Plano de Implementação — Itens Pendentes da Auditoria

**Data:** 2026-05-18  
**Branch:** `fix/auditoria-tecnica`  
**Referência:** `relatorio.md` — Seção 7

---

## Fase 1 — Infraestrutura (pré-requisitos)

### 1.1 — IMP-01: Framework de Logging

**Arquivo a criar:** `src/utils/logger.py`  
**Impacto:** Todos os módulos que usam `print()` para erros  

**Plano:**
1. Criar módulo `logger.py` com `logging.getLogger("vader")` configurado
2. Substituir todos os `print(f"[VADER]...")` e `print(f"Erro...")` por chamadas ao logger
3. Arquivos afetados: `components/__init__.py`, `dtc_parser.py`, `trimm_converter.py` (archive), `video_converter.py`

### 1.2 — DUP-01: Função `_safe()` centralizada

**Arquivo a criar:** `src/utils/helpers.py`  
**Impacto:** `components/__init__.py` (3 ocorrências), `plots.py` (1 ocorrência)

**Plano:**
1. Criar `safe_numeric()` em `src/utils/helpers.py`
2. Importar e substituir as 4 closures `_safe()` locais
3. Manter a assinatura compatível: `safe_numeric(source, key, fallback=0.0) -> float`

---

## Fase 2 — Eliminação de Duplicações

### 2.1 — DUP-02: Estilos DTC centralizados

**Arquivo a criar:** `src/ui/components/dtc_styles.py`  
**Impacto:** `views/dtc.py`, `views/completa.py`

**Plano:**
1. Extrair `highlight_status_t()`, `highlight_test_1()` e `aplicar_estilos()` para módulo dedicado
2. A função `aplicar_estilos(df)` recebe o DataFrame e retorna o Styler pronto
3. Remover definições duplicadas de ambas as views

### 2.2 — DUP-03: Painel de vídeo unificado

**Arquivo afetado:** `views/completa.py`  

**Plano:**
1. Criar função `_render_video_panel(title, videos, rotate, key_prefix)` dentro de `completa.py`
2. Substituir os blocos EICAS (linhas 24-65) e CHVC (linhas 67-108) por chamadas à função
3. Diferenças parametrizadas: `title`, `rotate`, `key_prefix`

### 2.3 — DUP-04: Cor de motor unificada

**Arquivo afetado:** `components/__init__.py`, `plots.py`  

**Plano:**
1. A função canônica já existe em `plots.py` como `EngineGaugePlotter._get_color()`
2. Extrair para função de módulo `get_engine_color(value, variable)` em `plots.py`
3. Importar em `components/__init__.py` e remover `_get_engine_color()` local

---

## Fase 3 — Correções Menores

### 3.1 — BUG-08: Roteador não define `modo_app` para VADR

**Arquivo:** `app.py`  
**Plano:** Setar `st.session_state.modo_app = "vadr"` no bloco elif do VADR

### 3.2 — DEAD-05: AttitudeIndicator como TODO

**Arquivo:** `components/__init__.py`  
**Plano:** Adicionar comentário `# TODO` documentando uso futuro

### 3.3 — IMP-07: FlightMap instanciado como constante de módulo

**Arquivo:** `views/vadr.py`  
**Plano:** Mover instanciação para nível de módulo `_FLIGHT_MAP = FlightMap()`

---

## Fase 4 — Melhorias de Arquitetura (IMP-03..09)

### 4.1 — IMP-09: Validação de estrutura CSV

**Arquivo:** `data_loader.py`  
**Plano:** Adicionar checagem de colunas TIME/STIME após leitura

### 4.2 — IMP-05: Imports no topo dos módulos

**Arquivos:** `landing.py`, `completa.py`  
**Plano:** Mover imports de `DtcParser`, `video_converter`, `local_scanner` para o topo

### 4.3 — IMP-02: Estrutura de testes (skeleton)

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
