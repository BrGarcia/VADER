# ROADMAP — V.A.D.E.R.
**Visualizador Analítico de Dados de Engenharia e Rastreio**
Versão: 1.5 | Atualizado: 10 de Abril de 2026

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

### Próximos Passos
- [ ] **Avisos Sonoros (Audio Alerts):** Implementação de Master Caution chime e alertas de voz para falhas críticas (ex: "FIRE", "OIL PRESSURE").
- [ ] **Alternância de Módulos:** Botão para alternar entre Horizonte Artificial e Painel de Alertas no box central.
- [ ] **Exportação de Relatórios:** Geração de PDF com resumo das falhas encontradas no voo.
- [ ] **Modo Comparativo:** Carregamento de dois voos simultâneos para comparação de performance.

---

## Arquivos de Referência para a Equipe

| Documento | Conteúdo |
|-----------|----------|
| `SCS.md` | Especificação completa de requisitos (RF, UI, RNF) |
| `Dicionario_de_Dados_VADER.md` | Mapeamento de variáveis CSV por fase |
| `10ABR.MD` | Detalhamento técnico das mudanças de hoje |
