# Dicionário de Dados e Plano de Implementação - V.A.D.E.R.
**Projeto:** Visualizador Analítico de Dados de Engenharia e Rastreio
**Referência Técnica:** Manual de Manutenção A-29 (Sistema FDR/CVR)
**Schema de Telemetria:** `docs/aircraft_telemetry_schema_v1.json`
**Versão:** 2.0

---

## Objetivo deste Documento
Este Dicionário de Dados serve como o guia definitivo para a equipe de engenharia de software. O arquivo CSV extraído do equipamento VADR possui 258 colunas brutas. As variáveis estão classificadas por **sistema** e **tipo de sinal**, conforme o schema `aircraft_telemetry_schema_v1.json`. Para garantir uma entrega ágil e funcional, o desenvolvimento é focado em **Fases de Implementação**.

---

## 📡 Classificação de Tipos de Sinal

O schema de telemetria classifica cada variável em um dos seguintes tipos:

| Tipo | Descrição | Tratamento no V.A.D.E.R. |
| :--- | :--- | :--- |
| **`analog`** | Sinal contínuo com valor numérico (float/int). Ex: altitude, temperatura, velocidade. | Plotagem em gráfico de linha contínuo. Eixo Y numérico. |
| **`digital`** | Sinal discreto binário ou enumerado (0/1 ou estados). Ex: WOW, flags de falha, armamento. | Detecção de eventos, marcadores no gráfico, cards de status. |
| **`metadata`** | Variáveis de tempo e identificação do registro. Não são dados de voo em si. | Eixo X (TIME/STIME) e cabeçalho do voo. |
| **`mixed`** | Variáveis que podem ser analógicas (massas em kg) ou discretas (flags de modo). | Tratamento caso a caso. Ver seção de sistemas. |
| **`status`** | Variáveis de qualidade/validação de dado (sufixo `V`). | Filtragem de dados inválidos. |

> **Nota:** Campos terminados em `V` (ex: `BALTV`, `NGV`) indicam a **matriz de validade** do parâmetro principal. Valores `0` ou `3` (octal) indicam dado válido, dependendo do sistema.

---

## 🗂️ Índice por Sistema — Schema `aircraft_telemetry_schema_v1.json`

### ⏱ `time` — Metadados / Temporais
**Tipo:** `metadata`

| Variável | Descrição |
| :--- | :--- |
| `Rec #` | Número do registro (linha) |
| `TIME` | Timestamp principal — **Eixo X Mestre de todas as visualizações** |
| `STIME` | Timestamp em formato string |
| `GMT_HOUR` / `GMT_MIN` / `GMT_SEC` | Hora UTC |
| `VADR_HOURS` / `VADR_MINUTES` / `VADR_SECOND` | Relógio interno do VADR |
| `VADR_DAY` / `VADR_MONTH` / `VADR_YEAR` | Data do voo |

---

### ✈️ `flight_dynamics` — Dinâmica de Voo
**Tipo:** `analog`

| Variável | Descrição | Faixa | Unidade |
| :--- | :--- | :--- | :--- |
| `NX` | Aceleração Longitudinal | -5G a +5G | G |
| `NY` | Aceleração Lateral | -2G a +2G | G |
| `NZ` | Aceleração Vertical (Força G) | -5G a +5G | G |
| `MACH` | Velocidade Mach | 0 a +4,09 | M |
| `AS` | Velocidade do Ar | 0 a 1023,9 | nós |
| `GSDEV` | Desvio GS (Instrument Landing) | — | DDM |
| `AOA` / `AOAV` | Ângulo de Ataque / Validade | -180 a +179,8 | ° |
| `QA` / `QAV` | Torque exigido (PMU) / Validade | 0 a 255 | % |
| `Q` / `QV` | Torque medido / Validade | 0 a 255 | % |
| `QT` / `QTV` | Torque controle PMU / Validade | 0 a 255 | % |
| `AYR` / `AYRV` | Taxa de Guinada / Validade | -512 a +511,98 | °/s |

---

### 🧭 `navigation` — Navegação
**Tipo:** `analog`

| Variável | Descrição | Faixa | Unidade |
| :--- | :--- | :--- | :--- |
| `GPSLAT` / `LATV` | Latitude GPS / Validade | -90 a +90 | ° |
| `GPSLONG` / `LONGV` | Longitude GPS / Validade | -180 a +180 | ° |
| `MAG_HDG` / `MAG_HDGV` | Proa Magnética / Validade | -180 a +180 | ° |

---

### 📏 `altimetry` — Altimetria
**Tipo:** `analog`

| Variável | Descrição | Faixa | Unidade |
| :--- | :--- | :--- | :--- |
| `PALT` / `PALTV` | Altitude Pressão / Validade | 0 a +131.071 | ft |
| `RAD_ALT` / `RAD_ALTV` | Radioaltímetro / Validade | 0 a +5000 | ft |
| `BALT` / `BALTV` | Altitude Barométrica / Validade | 0 a +131.071 | ft |
| `ALTR` / `ALTRV` | Taxa de Altitude / Validade | -32.768 a +32.754 | ft/min |

---

### 🔧 `engine` — Motor (Analógico)
**Tipo:** `analog`

| Variável | Descrição | Faixa | Unidade |
| :--- | :--- | :--- | :--- |
| `NG` / `NGV` | Velocidade Gerador de Gás / Validade | 0 a 255 | % RPM |
| `NP` / `NPV` | Velocidade da Hélice / Validade | 0 a 255 | % RPM |
| `ITT` / `ITTV` | Temperatura Inter-Turbinas / Validade | 0 a 2047 | °C |
| `FF` / `FFV` | Fluxo de Combustível / Validade | 0 a 500 | kg/h |
| `OP` / `OPV` | Pressão do Óleo / Validade | 0 a 200 | psi |
| `OT` / `OTV` | Temperatura do Óleo / Validade | -50 a +150 | °C |
| `T1` / `T1V` | Temperatura Entrada Motor / Validade | 0 a 127 | °C |

---

### ⛽ `fuel_and_pressure` — Pressões e Combustível
**Tipo:** `analog`

| Variável | Descrição | Faixa | Unidade |
| :--- | :--- | :--- | :--- |
| `TPRES` / `TPRESV` | Pressão Total / Validade | 0 a 2047,9 | hPa |
| `SPRES` / `SPRESV` | Pressão Estática / Validade | 0 a 2047,9 | hPa |
| `USPRES` / `USPRESV` | Pressão Upstream / Validade | — | — |
| `PS_FR` / `PS_FRV` | Pressão Combustível Restante / Validade | — | — |

---

### 🌡️ `environment` — Pressão Barométrica Ambiente
**Tipo:** `analog`

| Variável | Descrição |
| :--- | :--- |
| `BARO1` / `BARO1V` | Barômetro 1 / Validade |
| `BARO2` / `BARO2V` | Barômetro 2 / Validade |

---

### 🕹️ `flight_controls` — Superfícies de Controle
**Tipo:** `analog`

| Variável | Descrição | Faixa | Unidade |
| :--- | :--- | :--- | :--- |
| `AIL_POS` | Posição do Aileron | -17 a +15,9 | ° |
| `ELE_POS` | Posição do Profundor | -18,2 a +12,1 | ° |
| `RUD_POS` | Posição do Leme | -25 a +25 | ° |
| `FLAP` / `FLAPV` | Posição do Flape (0=Baixo, 2=Cima) / Validade | Octal 0/2 | — |

---

### 🤖 `autopilot_and_modes` — Modos de Sistema
**Tipo:** `digital`

| Variável | Descrição |
| :--- | :--- |
| `MODE_AD_AID` | Modo Aid do Autopiloto |
| `MODE_ALIGN` | Modo de Alinhamento |
| `MODE_INIT` | Modo de Inicialização |
| `MODE_MAINT` | Modo de Manutenção |
| `MODEV` | Validade dos bits de modo |
| `SYS_MODE` / `SYS_MODEV` | Modo de Sistema / Validade |

---

### 🛬 `landing_and_airframe` — Trem de Pouso e Airframe
**Tipo:** `digital`

| Variável | Lógica | Descrição |
| :--- | :--- | :--- |
| `WOW` | 0=Solo / 1=Ar | Weight on Wheels — fase de voo |
| `LDG` | **0=Abaixado** / 1=Recolhido | Trem de Pouso (**lógica invertida**) |
| `CANOPY` | 0=Aberta / 1=Fechada | Estado da Capota |
| `AIRBRK` | 0=Recolhido / 1=Aberto | Freio Aerodinâmico |
| `EMER` / `EMERV` | 0=Normal / 1=Emergência | Barra de Emergência / Validade |

---

### 🔥 `engine_discrete` — Motor (Discretos)
**Tipo:** `digital`

| Variável | Lógica | Descrição |
| :--- | :--- | :--- |
| `ENG_START` | 0=Em partida / 1=Sem partida | Flag de partida do motor |
| `ENGFIRE` | 0=Normal / 1=Fogo | Detecção de fogo no motor |
| `BLDAIR` | 0=Desativado / 1=Ativo | Ar de Sangria do Motor |
| `HFPTT` | — | Flag discreta PMU |

---

### 🚀 `weapons` — Armamento
**Tipo:** `digital`

Variáveis de pilones (`PY1` a `PY5`) e canhões (`GUN_1`, `GUN_2`).

| Prefixo | Sufixos | Descrição |
| :--- | :--- | :--- |
| `PY1`–`PY5` | `_QUANT`, `_RACK`, `_STATUS`, `_WEAPON` | Status, tipo e quantidade nos pilones |
| `CUR_WPN` | `_CAGE`, `_COCK`, `_FUZE`, `_MALF`, `_PROF`, `_RANG`, `_SIGH`, `_STAT`, `_STEP`, `_TRIG`, `_WRB` | Armamento selecionado atualmente |
| `GUN_1`, `GUN_2` | `_COCK`, `_COUNT`, `_MALF`, `_RANGE`, `_SEL`, `_SIGHT` | Estado das metralhadoras |

---

### ⚠️ `maintenance_warnings` — Palavras de Manutenção (MW1/MW2/MW3)
**Tipo:** `digital` — **Lógica: 0 = Normal, 1 = Falha**

Reportadas pela PMU. Validadas por `MW1V`, `MW2V`, `MW3V = 0`.

| Palavra | Exemplos de Bits | Domínio de Falha |
| :--- | :--- | :--- |
| **MW1** | `FPS1`, `FPS1ADC`, `FMNADC`, `FT1`, `FNG`, `FNP`, `FQ`, `FLUART1/2`, `FOATADC` | Sensores da PMU, ADC, temperatura, Ng/Np, comunicação |
| **MW2** | `FWF`, `FPCL`, `FAPCL`, `FDCDIS`, `FSTRTDIS`, `FRIGDIS`, `FWOW`, `FCREEP`, `FDCU`, `FLOWVOLT` | Combustível, PCL, discreta sensor WOW, tensão baixa, creep |
| **MW3** | `FWFLOOP`, `FBALOOP`, `FPIUTM`, `FFMUSM`, `FNPCSA`, `FPMUHW`, `FAILEEWR`, `FSHUTDIS` | Loop combustível/ar sangria, hardware PMU, solenoide de corte |

---

### 🔀 `misc` — Variáveis Mistas
**Tipo:** `mixed` (analógico + discreto conforme variável)

Inclui compensadores de voo, massas nos pilones e parâmetros de modo:

| Variável | Tipo | Descrição |
| :--- | :--- | :--- |
| `ATP` / `ATPV` | Analógico | Compensação do aileron (0–100%) |
| `RTP` / `RTPV` | Analógico | Compensação do leme (0–100%) |
| `APR` / `APRV` | Analógico | Compensação do profundor (0–100%) |
| `ARA` / `ARAV` | Analógico | Ângulo de Rolamento / Validade |
| `ARR` / `ARRV` | Analógico | Taxa de Rolamento / Validade |
| `LOPM`, `LIPM`, `CLPM`, `RIPM`, `ROPM` | Analógico | Massa nos pilones (kg) — esquerda-externa a direita-externa |
| `LDEV` / `LDEVV` | Analógico | Desvio LOC / Validade |

---

### ✅ `data_quality` — Qualidade do Dado
**Tipo:** `status`

| Variável | Descrição |
| :--- | :--- |
| `VALIDARINC` | Validade global dos dados recebidos via barramento ARINC-429 |

---

## 🚀 FASE 1: Núcleo de Dinâmica de Voo (MVP)
**Meta:** Ingestão do CSV, controle de tempo (eixo X) e plotagem do comportamento dinâmico.

| Variável | Sistema | Tipo | Descrição | Range | Tratamento |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TIME` / `STIME` | `time` | metadata | Timestamp | — | **Eixo X Mestre** |
| `BALT` | `altimetry` | analog | Altitude Barométrica | 0–131.071 ft | Eixo Y primário |
| `MACH` | `flight_dynamics` | analog | Velocidade Mach | 0–4,09 M | Eixo Y de velocidade |
| `AOA` | `flight_dynamics` | analog | Ângulo de Ataque | -180 a +179,8° | Atitude aerodinâmica |
| `NZ` | `flight_dynamics` | analog | Força G Vertical | -5 a +5G | Alerta visual se > 4,0G |
| `WOW` | `landing_and_airframe` | digital | Ar/Solo | 0=Solo / 1=Ar | Fases de pouso/decolagem |
| `LDG` | `landing_and_airframe` | digital | Trem de Pouso | **0=Baixo** / 1=Recolhido | ⚠️ Lógica invertida |

---

## ⚙️ FASE 2: Módulo do Grupo Motopropulsor

| Variável | Sistema | Tipo | Descrição | Range | Unidade |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Q` | `flight_dynamics` | analog | Torque medido | 0–255% | % |
| `NP` | `engine` | analog | Velocidade da Hélice | 0–255% | % RPM |
| `NG` | `engine` | analog | Velocidade Gerador de Gás | 0–255% | % RPM |
| `ITT` | `engine` | analog | Temperatura Inter-Turbinas | 0–2047°C | °C |
| `FF` | `engine` | analog | Fluxo de Combustível | 0–500 kg/h | kg/h |
| `OT` | `engine` | analog | Temperatura do Óleo | -50–150°C | °C |
| `OP` | `engine` | analog | Pressão do Óleo | 0–200 psi | psi |

---

## 🚨 FASE 3: Módulo de Diagnóstico e Falhas (EICAS)

### 3.1 Mensagens EICAS (`MWC_DATA`)
A coluna `MWC_DATA` registra as mensagens Warning/Caution em decimais. Ver tabela completa em `VADR.md`.

### 3.2 Palavras Discretas de Falha (`MW1`, `MW2`, `MW3`)
Sistema: `maintenance_warnings` | Tipo: `digital` | **Lógica: 0 = Normal, 1 = Falha**

| Variável | Descrição da Falha |
| :--- | :--- |
| `MW1_FT1` | Perda do sensor de Temperatura T1 |
| `MW1_FNG` | Perda do sensor Ng |
| `MW2_FDCDIS` | Falha no sensor da fonte DC |
| `MW3_FPMUHW` | Falha de hardware da PMU |
| `MW3_FSHUTDIS` | Falha no solenoide de corte (Shutdown) |

**Ação no código:** Varrer colunas `MW*` no DataFrame e plotar `markers` no gráfico principal no timestamp exato em que o bit for `== 1`.

---

## 🔗 Referência do Schema

O arquivo `docs/aircraft_telemetry_schema_v1.json` é a **fonte de verdade** para:
- Identificar se uma variável é analógica (plotar como linha) ou digital (plotar como evento).
- Separar variáveis de validade (sufixo `V`) das variáveis de dado.
- Agrupar variáveis por sistema para os cards de subsistemas da UI.

```
aircraft_telemetry_schema_v1.json
└── systems
    ├── time             → metadata   (eixo X)
    ├── flight_dynamics  → analog     (NX, NY, NZ, MACH, AOA, Q...)
    ├── navigation       → analog     (GPS, HDG)
    ├── altimetry        → analog     (PALT, BALT, RAD_ALT, ALTR)
    ├── engine           → analog     (NG, NP, ITT, FF, OP, OT, T1)
    ├── fuel_and_pressure→ analog     (TPRES, SPRES, USPRES, PS_FR)
    ├── environment      → analog     (BARO1, BARO2)
    ├── flight_controls  → analog     (AIL_POS, ELE_POS, RUD_POS, FLAP)
    ├── autopilot_and_modes → digital (MODE_*, SYS_MODE)
    ├── landing_and_airframe→ digital (WOW, LDG, CANOPY, AIRBRK, EMER)
    ├── engine_discrete  → digital   (ENG_START, ENGFIRE, BLDAIR, HFPTT)
    ├── weapons          → digital   (PY1–PY5, CUR_WPN, GUN_1/2)
    ├── maintenance_warnings → digital (MW1_*, MW2_*, MW3_*)
    ├── misc             → mixed     (compensadores, massas pilones, ARA, ARR)
    └── data_quality     → status    (VALIDARINC)
```

---
**Versão 2.0 — Atualizado com `aircraft_telemetry_schema_v1.json`**