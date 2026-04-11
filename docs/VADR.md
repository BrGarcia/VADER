# SISTEMA DE REGISTRO DE DADOS DE VOO/ GRAVADOR DE VOZ DA CABINE (FDR/CVR)

## Introdução

O sistema FDR/CVR (Registrador de Dados de Vôo/Gravador de Voz da Cabine) é responsável pela gravação de diversos dados críticos de voo e sinais de áudio gerados na cabine. Esses dados gravados auxiliam nas investigações, possibilitam monitorar a fadiga da aeronave através de um programa dedicado e podem ser úteis, também, para investigações de falhas nos sistemas da aeronave.

A unidade VADR (Gravador de Dados e Voz) é a unidade principal do sistema FDR/CVR. Esta unidade possui interface ARINC (Aeronautical Radio Inc.) (ARINC-429), além de linhas para sinais analógicos e discretos. A unidade VADR armazena:
* 2 h de dados de áudio 
* 25 h de dados de voo 

A unidade VADR possui entradas para barramentos ARINC-429, entradas para dispositivos que geram sinais analógicos e para os que geram sinais discretos. Todos os dados coletados pela unidade VADR são armazenados em uma memória protegida contra impacto e são lidos somente com a aeronave no solo, utilizando-se um EAS (Equipamento de Apoio no Solo).

### Visão Geral das Interfaces do VADR 
* **Entradas:** ASP do Posto Dianteiro, ASP do Posto Traseiro, Barramentos ARINC 429, Dispositivos que geram sinais analógicos, Dispositivos que geram sinais discretos.
* **Saídas:** Dados para Investigação de Acidentes, Dados para Cálculo de Fadiga da Aeronave.

---

## Descrição Geral

O sistema de FDR/CVR é uma combinação dos seguintes sistemas:
* FDR (Gravador de Dados de Vôo) 
* CVR (Gravador de Voz da Cabine) 

Assim, as funções da unidade VADR são coletar, comprimir, condicionar e armazenar dados recentes de voo e de áudio, ou seja:
* **Função FDR:** Registra os dados de voo das últimas 25 h.
* **Função CVR:** Registra os dados de áudio da cabine das últimas 2 h.

A gravação dos dados é circular, ou seja, quando a capacidade da memória interna é excedida, os dados novos são gravados sobre os dados mais antigos. O sistema de FDR/CVR começa a gravação dos dados de áudio no instante da energização da aeronave e continua este processo até 5 minutos após a detecção dos seguintes eventos:
* Ng (Velocidade do Gerador de Gás) menor do que 30%; WOW (Peso nas Rodas) indicando aeronave no solo.

> **NOTA:** Se a aeronave foi energizada, mas não realizou voo, o sistema de FDR/CVR grava dados de áudio da cabine enquanto ela estiver energizada.

O FDR/CVR inicia a gravação dos dados de voo quando um dos eventos seguintes ocorrer:
* Partida do motor 
* Ng maior que 30% 
* O bit de validação da partida do motor ("start valid"), proveniente do barramento da PMU (Unidade de Gerenciamento de Potência) assume estado lógico verdadeiro.

O processo de gravação dos dados de voo é encerrado 5 minutos após a detecção da Ng menor do que 30% com a lógica WOW indicando aeronave no solo.

Além do VADR, o sistema FDR/CVR possui um balizador acústico, um acelerômetro triaxial e sensores que detectam o movimento das superfícies de controle (tipo RVDT). O ULB (Balizador Acústico) ajuda na localização do VADR submerso. O acelerômetro triaxial efetua medidas de movimentação nos três eixos. Os RVDTs detectam o movimento do aileron, profundor e leme.

Algumas funções de controle estão disponíveis no MAINTENANCE PANEL (compartimento de bagagem), contendo chave para apagar áudio gravado e um conjunto (chave e LED) para teste da unidade. No DATA LOAD PANEL existe tomada para fone de ouvido (monitorar áudio) e um conector para descarregamento de dados.

Se detectada falha, a mensagem FDR FAIL é apresentada nas páginas PFL e BIT do CMFD.

---

## Componentes

O sistema possui os seguintes componentes:
* VADR 
* ULB 
* Acelerômetro triaxial 
* Sensores do tipo RVDT 

### Gravador de Dados e Voz (VADR) 
Instalada na estrutura acima do compartimento eletrônico. A principal característica é a memória de armazenamento resistente a impactos. Comunica-se através de interfaces: Analógicas, Discretas, Barramentos ARINC 429, Entradas de áudio e Barramento RS-422. A memória é do tipo "flash" EEPROM. Possui um relógio/calendário interno alimentado por bateria própria, ajustado via interface RS-422.

### Balizador Acústico (ULB) 
Instalado na face externa do VADR. Opera ao entrar em contato com água, transmitindo sinal de 37,5 kHz com alcance de até 2 NM por 30 dias.

### Acelerômetro Triaxial 
Efetua medições de aceleração nos eixos longitudinal, lateral e vertical. Possui três sensores sísmicos e é conectado ao VADR via interface analógica.

### Sensores RVDT 
Transdutor eletromecânico excitado por corrente DC. Há três RVDTs para detectar o movimento do aileron, profundor e leme.

---

## Operação

### Função FDR 
Recebe e grava dados de voo gerados por dispositivos (capacidade 25h). Os dados são compactados. Inicia a gravação com partida do motor, Ng > 30% ou bit "start valid" da PMU verdadeiro. Termina 5 minutos após Ng < 30% e WOW no solo.

### Função CVR 
Grava sinais de áudio da cabine (capacidade 2h). Inicia com energização e encerra 5 min após Ng < 30% e WOW no solo, ou ao desenergizar se não houve voo.

### Operações através da Interface RS-422 
Com um Laptop EAS, pode-se realizar:
* Atualização de programas (digital, voz, analógico) e dados de documentação do VADR.
* Descarregamento de dados de voo, áudio, fadiga e BIT.
* Inicialização do BIT, apagamento de dados e formatação.
* Ajuste de relógio e verificação de entradas.

### Autoteste (BIT) 
Executado na inicialização, continuamente e por comando. Falhas ativam a mensagem FDR FAIL e piscam/apagam o LED FDR/CVR BIT ABLE no MAINTENANCE PANEL.

---

## Controles e Indicações no Painel Maintenance

| N° | CONTROLE/INDICAÇÃO | FUNÇÃO DO CONTROLE/INDICAÇÃO |
| :--- | :--- | :--- |
| 1 | Chave CVR ERASE | Quando movida para a posição RESET, por alguns segundos, apaga completamente os dados de áudio gravados. |
| 2 | Chave FDR/CVR BIT | Quando movida para a posição TEST, executa um BIT da unidade VADR. |
| 3 | LED FDR/CVR BIT ABLE | Pisca durante o BIT e permanece aceso em seguida. Se permanecer apagado ou se acender sem piscar, significa falha no sistema. |

---

## Parâmetros do VADR

Lidos pelo programa IGS (Software EAS 440) no formato tabular ou gráfico. Dependem de uma matriz de validade (2 bits: 00, 11 / octal 0, 3) que valida o dado.

### Parâmetros de Voo (Controle Básico, Dados de Ar, Navegação, Atitude) 

| PARÂMETRO | DESCRIÇÃO | FAIXA / COMENTÁRIOS | MATRIZ DE VALIDADE |
| :--- | :--- | :--- | :--- |
| **AS+** | Velocidade do Ar Máxima | 0 a 1023,9375 nós. Resolução 0,625 nó | ASV=3 (válido) |
| **NZ** | Aceleração Vertical | -5G a +5G. Resolução 0,01G | N/A |
| **NY** | Aceleração Lateral | -2G a +2G. Resolução 0,01G | N/A |
| **NX** | Aceleração Longitudinal | -5G a +5G. Resolução 0,01G | N/A |
| **AIL_POS** | Posição do aileron | -17 a +15,9 graus. Resolução 0,32 grau | N/A |
| **ELE_POS** | Posição do profundor | -18,2 a +12,1 graus. Resolução 0,32 grau | N/A |
| **RUD_POS** | Posição do leme | -25 a +25 graus. Resolução 0,5 grau | N/A |
| **AIRBRK** | Freio aerodinâmico | Travado(1/0). Nível 1(aberto) / 0(terra) | N/A |
| **ATP** | Compensação do aileron | 0 a 100% (+25 a -25 graus) | ETPV=3 |
| **ETP** | Compensação do profundor | 0 a 100% (+25 a -25 graus) | ETPV=3 |
| **RTP** | Compensação do leme | 0 a 100% (+12,5 a -12,5 graus) | RTPV=3 |
| **APA** | Ângulo de arfagem | -180 a +179,99 graus | APAV=3 |
| **ARA** | Ângulo de rolamento | -180 a +179,99 graus | ARAV=3 |
| **AYR / APR / ARR** | Taxas atitude (Guinada/Arfagem/Rolamento) | -512 a +511,98 graus/s | AYRV/APRV/ARRV=3 |
| **MAG_HDG** | Proa magnética | -180 a +180 graus | MAG_HDGV=3 |
| **GPSLAT / GPSLON** | Latitude / Longitude GPS | -90 a +90 / -180 a +180 graus | LATV/LONV=3 |
| **LDEV / GSDEV** | Desvio LOC / Desvio GS | DDM (Diferença de Modulação) | LDEVV/GSDEVV=3 |
| **PALT / BALT** | Altitude pressão / Barométrica | Até +131.071 ft | PALTV/BALTV=3 |
| **MACH** | Número de Mach | 0 a +4,095 M | MACHV=3 |
| **ALTR** | Taxa de altitude | -32768 a +32754 ft/min | ALTRV=3 |
| **TPRES / SPRES** | Pressão Total / Estática | 0 a 2047,9 hPa | TPRESV/SPRESV=3 |
| **MODE** | Bit de estado (diversos modos BFI) | Estado Lógico (0 ou 1) | MODEV=0 |
| **AOA** | Ângulo de Ataque | -180 a +179,8 graus | AOAV=3 |
| **FLAP** | Posição do flape | Octal 0 (Baixo), Octal 2 (Cima) | FLAPV=0 |
| **RAD_ALT** | Radioaltímetro | 0 a +5000 ft | RAD_ALTV=3 |
| **EMER** | Tensão do Barramento Emergência | 0 a 31.875 VDC | EMERV=3 |

### Parâmetros de Missão - Armamento (Resumo) 
*Estes parâmetros referem-se às configurações dos pilones e canhões.*
* **PY1 a PY5:** Status geral dos pilones.
* **PYn_QUANT:** Quantidade de armamento/munição (10 bits) (Validado por PYnV=0).
* **PYn_RACK:** Tipo de rack instalado (0=Sem Rack, 1=LAU 7A/3, 5=LAU 3, 9=HMP/MRL70, etc).
* **PYn_STATUS:** Estado da carga (0=Sem carga, 1=Armamento disponível, 2=Erro, 3=Carga presa).
* **PYn_WEAPON:** Carga (0=Vazio, 1=Bomba, 2=Foguetes, 3=Tanque, 4/5/6=Casulos/Mísseis, 7=Casulo metralhadora).
* **CUR_WPN:** Seleção atual, travas (CAGE), detonador (FUZE), alcance (RANGE), miras (SIGHT) validados por CUR_WPNV=0.
* **GUN_1 / GUN_2:** Estado das metralhadoras (munição, falhas, miras, alcance) validados por GUN_1V/GUN_2V=0.
* **MASSAS:** LOPM, LIPM, CLPM, RIPM, ROPM indicam o peso nos pilones (kg). Validado por matrizes = 3 (Ex: LOPMV=3).

### Parâmetros de Motor e Combustível 
| PARÂMETRO | DESCRIÇÃO | COMENTÁRIOS | VALIDAÇÃO |
| :--- | :--- | :--- | :--- |
| **BLDAIR** | Ar de sangria | Nível lógico 1 (+28V) ou 0 (terra) | N/A |
| **ENG_START** | Partida do motor | 0 (partida) / 1 (sem partida) | N/A |
| **Q / QA / QT** | Torque (motor/exigido/sinal) | 0 a 255% | QV/QAV/QTV=3 |
| **T1 / ITT** | Temperaturas | T1 (0 a 127°C) / ITT (0 a 2047°C) | T1V/ITTV=3 |
| **NG / NP** | Velocidades (Ng/Np) | 0 a 255% (rpm) | NGV/NPV=3 |
| **PCL** | Manete de Potência | -20 a +179 graus | PCLV=3 |
| **FF / FR** | Fluxo e Combustível Restante | FF (0 a 500 kg/h) / FR (0 a 2047 kg) | FFV/FRV=3 |
| **OT / OP** | Temperatura/Pressão Óleo | OT (-50 a 150°C) / OP (0 a 200 psi) | OTV/OPV=3 |
| **DISD1_...** | Flags discretas (Start, Idle, Shutdown, etc.) | Provenientes da PMU (Estado 0 ou 1) | DISD1V=0 |

### Parâmetros de Manutenção 
* **CANOPY / LDG / WOW / ENGFIRE:** Sinais discretos para capota, trem de pouso, peso nas rodas e fogo no motor (N/A para matriz de validade).
* **Mensagens MW1, MW2, MW3:** Representam falhas diversas reportadas pela PMU (falha de sensores PS, ADC, TAT, Torque, falhas internas da PMU). Validadas por matrizes MW1V, MW2V e MW3V igual a 0.

---

## Mensagens de Alerta (Warning/Caution) e Arquitetura EICAS 

As mensagens de alerta ativadas e reportadas pelo EICAS (via parâmetro `MWC_DATA` com validação `MWCV=0`) são registradas decimalmente de 00 a 61.

| Mensagem | Descrição |
| :--- | :--- |
| **00** | Sem mensagens de alerta. |
| **01** | Falha nas unidades do motor, PMU (ENG_MAN). |
| **02** | Capota de pilotagem aberta (CANOPY). |
| **03 a 11** | (03) Sobrepressão CAB PRES, (04) Falha AP, (05) OIL PRES, (06) FUEL LVL, (07) BAT TEMP, (08) BLD LEAK, (09) CAB ALT, (10) OIL TEMP, (11) OXYGEN. |
| **12 a 20** | Relacionados a oxigênio, trem de emergência, transferência elétrica e combustível, pinos de segurança. |
| **23** | Combustível limite retorno base (BINGO). |
| **24 / 60** | CHIP DET (24 Caution / 60 Warning). |
| **32 / 33** | Gerador fora (GEN) / Pressão hidráulica baixa (HYD PRES). |
| **Outros** | 50 (BLD OVHT), 56 (FUEL IMB), 57 (ENG LMTS). |

*(A lista completa abrange de 01 a 61 detalhando todas as condições de ar, combustível, motor e elétrica indicadas no CMFD).*

---

## Monitor de Fadiga e Acelerações Verticais 

O sistema faz a atualização contínua de valores máximos e mínimos de parâmetros de voo atrelados à aceleração vertical (NZ), amostrado a 32Hz.

Parâmetros de fadiga registrados (cada um possui um N° de identificação):
* **04/05/06:** Aileron, Profundor e Leme (Max Up/Down, Max Left/Right).
* **30/31/32:** Compensadores correspondentes.
* **45 a 49:** Taxas e Ângulos de atitude.
* **15/19/20/50:** Torque, PCL, Np e AS+ (Velocidade Máxima).

### Contadores de Aceleração Vertical (NZ) 
Existem 20 contadores para NZ que incrementam ao ultrapassar "batentes" de G. 
* Contadores negativos vão de NZ -3.50 (Batente 0.00) até NZ -0.50.
* Contadores positivos vão de NZ +0.50 (Batente +1.00) até NZ +9.00 (Batente +3.50).

---

## Descarregamento e Análise de Dados 

O descarregamento dos dados requer um Laptop EAS utilizando o **Software IOGP (EAS 441)**. Para a análise (debriefing/manutenção), os dados armazenados são interpretados com o **Software IGS (EAS 440)**.

O **DATA LOAD PANEL** no compartimento de bagagem possui:
1. **Conector FDR/CVR DOWNLOAD:** Interface RS-422 para descarregamento de áudio/voo. 
2. **Conector CVR OUT:** Tomada de fone de ouvido para monitoramento direto do áudio. 