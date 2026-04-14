# Banco de Ideias — V.A.D.E.R.

Este arquivo serve para registrar sugestões, melhorias e novas funcionalidades identificadas durante o desenvolvimento. As ideias aqui listadas aguardam avaliação técnica e aprovação antes de serem movidas para o `ROADMAP.MD`.

---

## 🛠️ Diagnóstico e Segurança
### I-01: Monitoramento de Integridade do WOW
- **Descrição:** Integrar a flag de falha `MW2_FWOW` no card de Trem de Pouso.
- **Motivação:** Se o sensor de *Weight on Wheels* falhar, a indicação AR/SOLO torna-se não confiável.
- **Visual:** Exibir um aviso discreto "⚠️ SENSOR FAIL" no card quando `MW2_FWOW == 1`.

### I-16: Normalização da Lógica AR/SOLO (`WOW` → `PHASE`)
- **Descrição:** Criar uma camada de normalização que converta o valor bruto de `WOW` em um estado canônico `PHASE` (`ground` / `flight`) validado na ingestão.
- **Motivação:** A semântica de `WOW` é crítica para pouso, decolagem, flameout e filtros de análise. Centralizar essa regra evita inversões de lógica em dashboards e detecção de eventos.
- **Implementação sugerida:** No `DataLoader`, gerar `PHASE` a partir de `WOW`, validar a polaridade com trechos de CSV de referência e expor apenas `PHASE` para filtros de negócio e cards de UI.
- **Benefício:** Reduz erros de interpretação de fase de voo e torna as análises mais previsíveis.

### I-04: Inferência de Transição do Trem de Pouso
- **Descrição:** Criar uma lógica para detectar e exibir o estado "EM TRÂNSITO" do trem de pouso.
- **Motivação:** Como o CSV não fornece uma variável de transição, podemos inferir o movimento monitorando a mudança de estado da variável `LDG`.
- **Visual:** O rótulo mudaria para "EM TRÂNSITO..." em cor âmbar durante a mudança de estado.
- **Parecer:** Ainda nao se faz necessario porém podemos implementar um timer que conta quanto tempo o trem de pouso está em transição e se passar de um certo tempo (opor exemplo 5 segundos), exibir um alerta. verificar com tecnico da área qual o esse tempo limite.

### I-06: Verificação de Matriz de Validade (Octal 3)
- **Descrição:** Utilizar as colunas de validade (ex: `BALTV`, `MACHV`, `ITTV`) para validar as leituras.
- **Motivação:** Conforme o manual `VADR.md`, um dado só é confiável se sua matriz de validade for `3`. Se for `0`, o dado é inválido.
- **Visual:** Adicionar um indicador visual (ex: contorno tracejado ou cor cinza) quando o dado exibido estiver com flag de validade inválida no CSV.
- **Parecer:** Implementar na fase 5, na proxima revisao do arquivo IDEIAS.MD mover esse requisito para o ROADMAP.MD.

### I-07: Detecção Automática de Excedências (Over-G / ITT)
- **Descrição:** Algoritmo que varre o CSV no carregamento e lista todos os momentos onde limites estruturais (`NZ > 4.0G`) ou térmicos (`ITT > 1000°C`) foram ultrapassados.
- **Motivação:** Facilita o trabalho do inspetor de manutenção, que não precisa "procurar" a falha no gráfico.

### I-17: Auditoria de Integridade do Schema Canônico
- **Descrição:** Implementar uma verificação automática para comparar o header do CSV carregado com `docs/schemas/aircraft_telemetry_schema_v1.json`.
- **Motivação:** Hoje o schema é tratado como fonte de verdade, então qualquer divergência entre contrato e arquivo real pode quebrar views, filtros e o EICAS.
- **Implementação sugerida:** Na ingestão, listar colunas ausentes/extras e exibir um relatório de compatibilidade; em desenvolvimento, adicionar um teste automatizado que falhe quando o schema ficar desatualizado.
- **Benefício:** Evita deriva entre documentação, código e telemetria real, reduzindo regressões silenciosas.

---

## 🎨 Interface e Experiência (UX)
### I-02: Filtro de Alertas Ativos
- **Descrição:** Botão no `FaultPanel` para alternar entre "Ver Todos" (Ghosting) e "Apenas Ativos".

### I-08: Layout "Night Vision" (NVG Mode)
- **Descrição:** Alternar o esquema de cores para um tom verde monocromático de alta intensidade.
- **Motivação:** Simular a operação noturna com óculos de visão noturna, comum em missões do A-29.

### I-09: Marcadores de Eventos na Timeline
- **Descrição:** Permitir que o usuário clique no gráfico e adicione uma "Nota de Manutenção" em um timestamp específico.
- **Motivação:** Compartilhar insights entre diferentes inspetores sobre o mesmo voo.

---

## 📊 Analytics e Missão
### I-03: Cálculo de Distância de Pista
- **Descrição:** Estimar a distância percorrida no solo durante a corrida de decolagem/pouso.

### I-05: Monitoramento de Trajetória (Mapa GPS)
- **Descrição:** Plotar `GPSLAT` e `GPSLONG` em um mapa interativo sincronizado.

### I-10: Painel de Armamento (Store Management)
- **Descrição:** Visualização gráfica dos 5 pilones (`PY1` a `PY5`) mostrando o tipo de carga e peso remanescente.
- **Motivação:** Útil para debriefing de missões de ataque, correlacionando o disparo (`CUR_WPN_TRIG`) com a mudança de massa nos pilones.

### I-11: Contador de Ciclos do Motor
- **Descrição:** Implementar a lógica de contagem de ciclos (LCF - Low Cycle Fatigue) baseada nas variações de Ng e ITT conforme definido nos manuais de manutenção.
- **Motivação:** Automatizar o cálculo de vida fadigável do motor a partir da telemetria bruta.

---

## 📂 Dados e Performance
### I-12: Verificação de Integridade (MD5/SHA)
- **Descrição:** Gerar e verificar hashes dos arquivos CSV carregados.
- **Motivação:** Garantir que a telemetria não foi alterada maliciosamente entre o descarregamento da aeronave e a análise no V.A.D.E.R.

### I-13: Exportação de Relatório de Manutenção (PDF)
- **Descrição:** Botão para gerar um PDF consolidado com metadados da ANV, lista de falhas detectadas e estatísticas de uso (Tempo de voo, G máximo, ITT máximo).

### I-18: Política Segura de Cache e Retenção Local
- **Descrição:** Adicionar um modo de operação com cache controlado para CSV/Parquet e histórico de arquivos, com opção de retenção mínima.
- **Motivação:** O projeto trabalha com dados sigilosos; manter cópias derivadas e histórico sem política explícita aumenta o risco operacional.
- **Implementação sugerida:** Criar configurações como `sem cache`, `cache temporário da sessão` e `cache persistente`, além de rotina de expurgo e indicador visual mostrando onde os artefatos foram gravados.
- **Benefício:** Melhora a segurança operacional sem abrir mão de performance quando o ambiente permitir persistência.

### I-19: Forward-Fill Seletivo por Tipo de Sinal
- **Descrição:** Restringir o `ffill` apenas para variáveis analógicas sub-rate previamente aprovadas.
- **Motivação:** Propagar automaticamente estados discretos, flags de falha ou colunas de validade pode criar eventos artificiais e mascarar anomalias reais.
- **Implementação sugerida:** Manter uma whitelist no schema ou em configuração dedicada indicando quais colunas aceitam `ffill`, e registrar no Parquet quais transformações foram aplicadas.
- **Benefício:** Preserva a fidelidade da telemetria e torna a ingestão auditável.

## ⚡ Produtividade e Auditoria Rápida
### I-14: Smart Audit (Verificação de Excedência Direta)
- **Descrição:** Uma nova seção na Landing Page que permite ao usuário carregar um CSV e definir filtros específicos (ex: "NZ > 5.0" ou "ITT > 1050") antes de entrar na análise completa.
- **Motivação:** Economizar tempo quando o objetivo é apenas validar se um limite técnico foi violado.
- **Funcionalidade:** O sistema processa o arquivo, localiza os exatos timestamps que satisfazem a condição e gera um gráfico simplificado focando apenas nesses eventos, ignorando o restante dos dados irrelevantes.

---

## 📟 Instrumentos e Displays

### I-15 (ex S-07): Integração do VSI — Velocidade Vertical
- **Descrição:** Integrar o componente `vsi.py` (classe `VerticalSpeedIndicator`, já implementado e funcional) ao `AttitudeBox`, exibindo o indicador de velocidade vertical no painel de voo.
- **Motivação:** O componente está pronto e testado (possui até um modo demo standalone). A variável `ALTR` (taxa de altitude, ft/min) já é gravada pelo VADR e coberta pelo dicionário de dados.
- **Implementação sugerida:** Adicionar um quinto card no `SubsystemCards`, ou incluir o gauge VSI na coluna de dados de voo do `AttitudeBox` abaixo do AOA.
- **Referência:** `src/ui_components/vsi.py` — classe `VerticalSpeedIndicator`, faixa -3000 a +3000 ft/min.

### I-20: Snapshot Temporal Estável para Componentes
- **Descrição:** Evoluir o controle temporal para trabalhar com um snapshot estável de amostra, em vez de depender apenas do índice global do DataFrame.
- **Motivação:** Reordenação, filtros, troca de arquivo e comparação entre voos podem desalinhar componentes quando todos dependem do mesmo índice bruto.
- **Implementação sugerida:** Criar um objeto de snapshot com `record_id`, `TIME`, `STIME` e linha resolvida, repassando esse objeto aos componentes de UI em vez de cada módulo consultar o índice diretamente no `session_state`.
- **Benefício:** Aumenta a robustez do sincronismo entre gráficos, cards e painéis, além de facilitar testes e evolução futura para modo comparativo.

