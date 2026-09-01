# Implementação e Análise de Dados TRIMM - V.A.D.E.R.

Este documento detalha o progresso da integração dos dados da pasta `TRIMM/` e o plano para a funcionalidade de detecção de atuação não comandada.

> ⚠️ **Atualizado em 01/09/2026:** `trimm_converter.py` e `trimm_analysis.py` (Seção 1 abaixo) foram movidos para `archive/` — não são mais importados em lugar nenhum do código. O fluxo em produção hoje é `src/data/dtc_parser.py` (`DtcParser`), documentado em `docs/DTC_CONVERSOR_DMP.md`. Esta seção fica como registro histórico da fase exploratória.

## 1. Conquistas Atuais (Fase de Exploração e Pesquisa)

### 1.1. Conversão e Consolidação
- **Arquivo:** `src/data/trimm_converter.py`
- **Ação:** Criado script para ler arquivos `TRIMM00*.DMP` (formato texto com separador `;`), consolidar em ordem cronológica e salvar como `data/raw/TRIMM_COMBINED.csv`.
- **Compatibilidade:** 
    - Aplicação de cabeçalho específico: `UTC;Hora;Emer_ON;Emer_SW;Stick_FWD;Stick_AFT;CAS;TAS;GS;BARO;RALT;PITCH_ANG;ROLL_ANG;AIL_T_POS;ELEV_T_POS;RUD_T_POS;PITCH_MIS;ROLL_MIS;Yellow_Zone`.
    - Mapeamento de aliases para compatibilidade com a UI do VADER (ex: `PITCH_ANG` -> `APA`).
    - Geração de metadados e linha de unidades dummy para suporte pelo `DataLoader` existente.

### 1.2. Lógica de Análise (Atuação Não Comandada)
- **Arquivo:** `src/data/trimm_analysis.py`
- **Algoritmo:**
    - Identifica estado ativo dos manches (`Stick_FWD` ou `Stick_AFT`).
    - Calcula o gradiente (delta) das superfícies (`AIL_T_POS`, `ELEV_T_POS`, `RUD_T_POS`) e atitude (`ROLL_ANG`, `PITCH_ANG`).
    - **Detecção:** Marca como `UNCOMMANDED_ACT` qualquer variação significativa de superfície/atitude enquanto o manche está inativo (`FALSE`).
- **Resultados Preliminares:** Detectadas 703 ocorrências de atuação não comandada no dataset `TRIMM_COMBINED.csv`.

---

## 2. Plano de Implementação (Próximos Passos)

### Fase A: Integração Transparente na UI
1. **Auto-Detecção:** Modificar o `DataLoader` para identificar arquivos originados do TRIMM e aplicar automaticamente o `TrimmAnalyzer`.
2. **Visualização de Alertas:** 
    - Adicionar faixas de fundo (vbands) vermelhas no `TimelinePlotter` quando `UNCOMMANDED_ACT` for True.
    - Criar um card de status específico no `SubsystemCards` para "Integridade de Comandos".

### Fase B: Análise Cruzada (Cross-Check VADR)
1. **Sincronização Temporal:** Criar utilitário para alinhar o `UTC` do TRIMM com o `TIME`/`GMT` do CSV do VADR.
2. **Correlação de Causa:** Verificar se atuações não comandadas coincidem com picos de pressão hidráulica ou falhas elétricas (`MWC_DATA`) registradas no VADR.

### Fase C: Automação
1. **Watchdog:** Implementar trigger para que, ao detectar novos arquivos `.DMP` na pasta `TRIMM/`, o sistema gere automaticamente o `.csv` consolidado.

---

## 3. Notas Técnicas
- **Limiares de Sensibilidade:** Atualmente em 0.5° (superfícies) e 0.2° (atitude). Podem ser ajustados conforme o nível de ruído dos sensores.
- **Estrutura de Arquivos:** Os arquivos `.DMP` são lidos como strings para evitar erros de tipo com valores como `X.X` e `F/T`.
