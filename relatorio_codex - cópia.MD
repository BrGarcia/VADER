# Relatório Codex

## Escopo

Revisão dos artefatos em `docs/` com foco em correção, segurança e arquitetura. A análise foi baseada principalmente em:

- `docs/02_requirements.md`
- `docs/03_architecture.md`
- `docs/04_data_model.md`
- `docs/05_decisions.md`
- `docs/ROADMAP.md`
- `docs/schemas/*.json`
- `docs/CSV/EXEMPLO_CSV.csv`

## Achados

### 1. Crítico
**Schema declarado como fonte de verdade não cobre o formato real do CSV nem os fluxos documentados**

**Evidência**
- `docs/04_data_model.md:279` declara que `aircraft_telemetry_schema_v1.json` é a fonte de verdade.
- `docs/04_data_model.md:259-273` documenta `MWC_DATA` como parte do módulo EICAS.
- `docs/01_vision.md:17` e `docs/Guia_UI_EICAS.md:39-43` também dependem de `MWC_DATA`.
- O CSV real inclui várias colunas ausentes no schema, por exemplo `MWC_DATA`, `MWCV`, `PCL`, `PCLV`, `MACHV`, `APA`, `APAV`, `ETP`, `ETPV`, `ASV`, `GSDEVV` e toda a família `DISD1_*` (`docs/CSV/EXEMPLO_CSV.csv:9`).
- Comparação automática entre o header do CSV e `docs/schemas/aircraft_telemetry_schema_v1.json` encontrou `39` colunas presentes no CSV e ausentes no schema.

**Impacto**
- Qualquer código que trate o schema como contrato canônico vai descartar sinais reais ou classificar incorretamente eventos.
- O módulo EICAS pode falhar por ausência de `MWC_DATA`/`MWCV` no contrato principal.
- A camada de ingestão e a UI ficam acopladas a exceções manuais fora do schema, o que enfraquece a arquitetura.

**Correção sugerida**
- Expandir `docs/schemas/aircraft_telemetry_schema_v1.json` para refletir integralmente o header real do CSV.
- Incluir explicitamente `MWC_DATA`, `MWCV`, `PCL`, `PCLV`, `MACHV` e os demais grupos ausentes, com tipo, categoria e semântica.
- Adicionar validação automatizada no CI comparando o schema com um CSV de referência.

### 2. Alto
**Visões analíticas referenciam variáveis inexistentes no schema oficial**

**Evidência**
- `docs/schemas/tipo_de_analise_v1.json:37` usa `PCL`.
- `docs/schemas/tipo_de_analise_v1.json:58-59` usa `MACHV`.
- `docs/schemas/aircraft_telemetry_schema_v1.json` não contém `PCL` nem `MACHV`.
- O `ROADMAP` afirma que `PCL` já é coluna central do produto (`docs/ROADMAP.md:53`, `docs/ROADMAP.md:82`).

**Impacto**
- Geração de dashboards e filtros a partir do schema pode quebrar com erro de coluna ausente.
- O conjunto de visões fica impossível de validar mecanicamente contra o contrato de dados.

**Correção sugerida**
- Corrigir o schema para incluir essas colunas, ou remover as referências das views até o contrato ser atualizado.
- Adicionar um teste de consistência entre `tipo_de_analise_v1.json` e `aircraft_telemetry_schema_v1.json`.

### 3. Alto
**Semântica de `WOW` está inconsistente e induz filtros errados**

**Evidência**
- `docs/04_data_model.md:156` define `WOW` como `0=Solo / 1=Ar`.
- `docs/schemas/tipo_de_analise_v1.json:24-29` define `hard_landing` com filtro `{ "WOW": 1 }`, o que pela própria documentação significa aeronave em voo.
- O mesmo arquivo usa `{ "WOW": 0 }` em `high_g_event` e `engine_flameout` (`docs/schemas/tipo_de_analise_v1.json:8-13`, `45-50`), o que muda completamente o recorte analítico.

**Impacto**
- Eventos de pouso duro, fases de voo e análises de solo/ar podem ser calculados com polaridade invertida.
- Esse tipo de erro afeta diretamente a correção do diagnóstico.

**Correção sugerida**
- Definir uma única semântica formal para `WOW` no schema principal.
- Trocar os filtros das views para usar uma abstração derivada, por exemplo `PHASE=ground|flight`, em vez de valor bruto de bit.
- Adicionar exemplos de verdade-terreno com trechos de CSV para validar a polaridade.

### 4. Alto
**Estratégia de `forward-fill` está ampla demais para sinais sensíveis**

**Evidência**
- `docs/03_architecture.md:27-31` diz que o loader aplica `forward-fill / ffill` para frequências mais lentas.
- `docs/05_decisions.md:8-11` repete a decisão de persistir dados já tipificados e preenchidos em Parquet.
- O conjunto de sinais inclui bits de falha, validade e estados discretos documentados em `docs/04_data_model.md`.

**Impacto**
- Aplicar `ffill` sem whitelist por variável pode fabricar permanência artificial de alertas, estados discretos e flags de validade.
- Como o resultado é salvo em Parquet, o erro deixa de ser transitório e passa a contaminar leituras subsequentes.

**Correção sugerida**
- Restringir `ffill` a uma lista explícita de sinais analógicos sub-rate.
- Proibir `ffill` para colunas de validade, falha, eventos e mensagens discretas.
- Persistir metadados de transformação no Parquet para auditoria da ingestão.

### 5. Alto
**Persistência local de dados sigilosos sem requisitos de proteção**

**Evidência**
- `docs/03_architecture.md:4` e `docs/02_requirements.md:27` justificam o produto por sigilo operacional e uso offline.
- `docs/05_decisions.md:10` manda persistir o cache em `data/processed/`.
- `docs/02_requirements.md:63` ainda exige histórico de arquivos carregados.
- `docs/ROADMAP.md:148` instrui apagar manualmente Parquets antigos, indicando retenção local sem política formal.

**Impacto**
- O desenho aumenta superfície de exposição local: cópias derivadas em Parquet, histórico de uso e necessidade de limpeza manual.
- Offline não equivale a seguro; sem requisitos de retenção, criptografia e descarte, há risco operacional claro.

**Correção sugerida**
- Especificar política de retenção, localização do cache, descarte seguro e opção de operação sem persistência.
- Criptografar artefatos em repouso quando o ambiente exigir.
- Tratar histórico de arquivos como funcionalidade opt-in e não como padrão.

### 6. Médio
**Controle temporal global por índice e `st.session_state` cria acoplamento frágil**

**Evidência**
- `docs/05_decisions.md:17-19` descreve um `TimeController` que injeta posição temporal em `st.session_state`.
- A decisão também afirma que o slider funciona como “Index universal”.

**Impacto**
- Qualquer filtragem, reordenação, reingestão ou troca de DataFrame pode invalidar o índice global e sincronizar componentes com a linha errada.
- O estado global implícito dificulta teste, previsibilidade e evolução para comparação entre voos.

**Correção sugerida**
- Trocar índice bruto por um identificador estável de amostra, como timestamp normalizado e/ou `record_id`.
- Encapsular o snapshot temporal em objeto imutável passado explicitamente aos componentes.
- Reservar `session_state` para estado de UI, não para identidade de dado.

### 7. Médio
**Artefatos de documentação e schema estão incompletos ou apontam para caminhos errados**

**Evidência**
- `docs/04_data_model.md:4` e `docs/04_data_model.md:279` apontam para `docs/aircraft_telemetry_schema_v1.json`, mas o arquivo real está em `docs/schemas/aircraft_telemetry_schema_v1.json`.
- `docs/schemas/variaveis.json` existe com tamanho zero.

**Impacto**
- Automação, onboarding e scripts de validação podem falhar por caminho inválido.
- Um arquivo JSON vazio sob `docs/schemas/` sugere contrato incompleto e pode quebrar consumidores que percorrem o diretório.

**Correção sugerida**
- Corrigir todos os paths para `docs/schemas/aircraft_telemetry_schema_v1.json`.
- Remover `variaveis.json` se não for usado, ou preenchê-lo com contrato válido.
- Adicionar verificação de integridade dos arquivos de schema no pipeline.

## Prioridade Recomendada

1. Corrigir o schema canônico e alinhar as views analíticas a ele.
2. Formalizar a semântica de `WOW` e revisar filtros derivados.
3. Restringir `ffill` e definir política de proteção/retenção do cache Parquet.
4. Reduzir acoplamento temporal por índice global.
5. Limpar caminhos e artefatos incompletos em `docs/schemas`.
