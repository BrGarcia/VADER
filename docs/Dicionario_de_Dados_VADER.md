# Dicionário de Dados e Plano de Implementação - V.A.D.E.R.
**Projeto:** Visualizador Analítico de Dados de Engenharia e Rastreio
**Referência Técnica:** Manual de Manutenção A-29 (Sistema FDR/CVR)
**Versão:** 1.0

## Objetivo deste Documento
Este Dicionário de Dados serve como o guia definitivo para a equipe de engenharia de software. O arquivo CSV extraído do equipamento VADR possui 258 colunas brutas. Para garantir uma entrega ágil e funcional, o desenvolvimento será focado em **Fases de Implementação**, isolando as variáveis necessárias para cada módulo da interface.

---

## 🚀 FASE 1: Núcleo de Dinâmica de Voo (O MVP)
**Meta da Sprint:** Construir a base da aplicação (ingestão do CSV usando Pandas), implementar o controle de tempo universal (eixo X) e plotar o comportamento dinâmico e espacial da aeronave.

| Variável CSV | Descrição Técnica | Unidade / Tipo | Range Operacional | Tratamento no Código (Lógica) |
| :--- | :--- | :--- | :--- | :--- |
| **TIME** / **STIME** | Timestamp (Linha do Tempo) | Tempo (String/Datetime) | Início ao Fim da Gravação | **Eixo X Mestre.** Todas as visualizações devem sincronizar com esta coluna. |
| **BALT** | Altitude Barométrica | Pés (ft) - Float | 0 a +131.071 ft | Eixo Y de Altitude. |
| **MACH** | Velocidade Mach | Número Mach - Float | 0 a +4.09 M | Eixo Y de Velocidade (ou usar `AS` para Knots). |
| **AOA** | Ângulo de Ataque | Graus (°) - Float | -180 a +179.8° | Plotagem de atitude aerodinâmica. |
| **APA** | Ângulo de Arfagem (Pitch) | Graus (°) - Float | -180 a +179.99° | Animar o eixo vertical do horizonte artificial. |
| **ARA** | Ângulo de Rolamento (Roll)| Graus (°) - Float | -180 a +179.99° | Animar a inclinação do horizonte artificial. |
| **NZ** | Aceleração Vertical (Força G) | Força G - Float | -5G a +5G | Indicador de Carga Estrutural (Criar alerta visual se > 4.0G). |
| **WOW** | Weight on Wheels (Ar/Solo)| Discreto - Booleano | 0 ou 1 | **0 = Aeronave no solo**. **1 = Aeronave no ar**. Usar para destacar fases de decolagem/pouso. |
| **LDG** | Trem de Pouso | Discreto - Booleano | 0 ou 1 | **ATENÇÃO À LÓGICA INVERTIDA:** **0 = Abaixado/Travado**, **1 = Recolhido**. |

---

## ⚙️ FASE 2: Módulo do Grupo Motopropulsor (Motor)
**Meta da Sprint:** Adicionar os cards e gráficos de análise de saúde e performance do motor, permitindo cruzar os comandos da manete com a resposta da turbina.

| Variável CSV | Descrição Técnica | Unidade / Tipo | Range Operacional | Tratamento no Código (Lógica) |
| :--- | :--- | :--- | :--- | :--- |
| **PCL** | Posição da Manete de Potência| Graus (°) - Float | -20 a +179° | Curva base de comando do piloto. |
| **Q** | Torque do Motor | % - Float | 0 a 255% | Resposta de performance primária. |
| **NP** | Velocidade da Hélice (Passo) | % (RPM) - Float | 0 a 255% | Rotação da hélice. |
| **NG** | Velocidade do Gerador de Gás | % (RPM) - Float | 0 a 255% | Rotação do motor térmico. |
| **ITT** | Temperatura Entre Turbinas | Celsius (°C) - Int | 0 a 2047°C | Indicador de saúde térmica primário. |
| **FF** | Fluxo de Combustível | kg/h - Float | 0 a 500 kg/h | Indicador de consumo instantâneo. |
| **OT** | Temperatura do Óleo | Celsius (°C) - Int | -50 a +150°C | Monitoramento de lubrificação. |
| **OP** | Pressão do Óleo | PSI - Float | 0 a 200 psi | Monitoramento de lubrificação. |

---

## 🚨 FASE 3: Módulo de Diagnóstico e Falhas (EICAS)
**Meta da Sprint:** Transformar a interface em uma ferramenta de *troubleshooting*, mapeando e traduzindo os códigos de erro da aeronave no tempo exato em que ocorreram.

### 3.1 Mensagens EICAS (Alerta à Tripulação)
A coluna **`MWC_DATA`** registra as mensagens (Warning/Caution) enviadas ao painel EICAS, utilizando códigos decimais.
* **Ação para o Desenvolvedor:** Criar um dicionário/hashmap de tradução.
* **Mapeamento Principal:**
    * `00` = Operação Normal (Sem alertas)
    * `01` = Falha PMU (ENG_MAN)
    * `05` = Pressão de óleo fora dos limites
    * `27` = Sobreaquecimento Eletrônico (ELEK OVH)
    * `47` = Fogo Detectado no Motor (FIRE)
    * `57` = Limites operacionais do motor atingidos

### 3.2 Palavras Discretas de Falha (Sensores e Módulos)
As colunas com prefixo `MW1`, `MW2` e `MW3` representam os bits de status (0 = Normal, 1 = Falha).
* **Ação para o Desenvolvedor:** Criar função que varre essas colunas no DataFrame e plota marcadores (`markers`) no gráfico principal exatamente no timestamp em que a variável for `== 1`.

| Exemplos CSV | Descrição da Falha | Lógica |
| :--- | :--- | :--- |
| **MW1_FT1** | Perda do sensor de Temperatura T1 | 1 = Falha |
| **MW1_FNG** | Perda do sensor Ng | 1 = Falha |
| **MW2_FDCDIS**| Falha no sensor da fonte DC | 1 = Falha |
| **MW3_FPMUHW**| Falha de hardware da PMU | 1 = Falha |
| **MW3_FSHUTDIS**| Falha no solenoide de corte (Shutdown)| 1 = Falha |

---
**Fim do Documento**