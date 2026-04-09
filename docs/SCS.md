# Especificação de Requisitos de Software (SRS)
## Sistema de Análise de Telemetria de Voo (VADER)

**Versão:** 1.0
**Data:** 09 de Abril de 2026

---

## 1. Introdução

### 1.1 Propósito
Este documento especifica os requisitos de software para o Visualizador Analítico de Dados de Engenharia e Rastreio. (VADER). O sistema é uma aplicação web local focada na ingestão, processamento e visualização interativa de dados gravados de voo (Flight Data Recorder) no formato *.csv, facilitando a inspeção técnica, análise estrutural e troubleshooting.

### 1.2 Escopo
O VADER processará arquivos CSV contendo logs de telemetria de alta densidade (ex: dados de aeronaves A-29). O software extrairá essas séries temporais e as apresentará em um painel interativo (Dashboard) dividido em módulos lógicos. O foco principal é fornecer correlação visual imediata entre os comandos do piloto, o comportamento dinâmico da aeronave e a resposta dos sistemas do motor/célula em qualquer instante de tempo do voo.

### 1.3 Público-Alvo
* Inspetores de Manutenção Aeronáutica
* Chefes de Oficina de Eletrônica/Aviônicos
* Engenheiros de Dados de Voo

---

## 2. Descrição Geral

### 2.1 Perspectiva do Produto
O VADER será uma aplicação independente (standalone) baseada em scripts Python, utilizando bibliotecas de renderização web (como Streamlit ou Dash) para a interface do usuário. Não exigirá conexão com a internet ou banco de dados externo, operando estritamente offline para garantir o sigilo dos dados operacionais.

### 2.2 Ambiente de Operação
* **Sistema Operacional:** Multiplataforma (suporte nativo para ambientes Windows e macOS).
* **Linguagem:** Python 3.9 ou superior.
* **Interface:** Navegador Web moderno (Chrome, Edge, Safari).

---

## 3. Requisitos Funcionais (RF)

### RF01: Ingestão e Tratamento de Dados
* **RF01.1:** O sistema deve permitir a leitura de arquivos delimitados (`.csv`) contendo cabeçalhos de metadados e tabelas de telemetria.
* **RF01.2:** O sistema deve ignorar automaticamente as linhas de cabeçalho inicial não estruturadas e identificar corretamente as colunas de dados.
* **RF01.3:** O sistema deve tratar dados ausentes (NaN) ou corrompidos sem causar falha total da aplicação.

### RF02: Módulo de Posição e Atitude (Box Superior)
* **RF02.1:** O sistema deve exibir uma representação gráfica minimalista do horizonte (céu/solo).
* **RF02.2:** O horizonte visual deve reagir de forma sincronizada aos dados de inclinação lateral (*Roll* / `AIL_POS` ou correlato) e arfagem (*Pitch* / `ELE_POS` ou correlato).
* **RF02.3:** Devem ser exibidos, em destaque numérico neste módulo, os dados críticos instantâneos: Altitude (`BALT`/`PALT`) e Velocidade (`MACH` ou *Airspeed*).

### RF03: Módulo de Análise Temporal (Box Central)
* **RF03.1:** O sistema deve plotar um gráfico cartesiano interativo bidimensional (2D).
* **RF03.2:** O Eixo X deve representar obrigatoriamente a linha do tempo do voo (`TIME`), do início ao fim da gravação.
* **RF03.3:** O sistema deve fornecer um menu de seleção (Dropdown) listando todas as colunas numéricas disponíveis no arquivo CSV.
* **RF03.4:** O Eixo Y deve exibir os valores da variável selecionada no menu pelo usuário.
* **RF03.5:** O gráfico deve permitir operações de *Zoom In*, *Zoom Out* e *Pan* (arrastar).

### RF04: Módulo de Subsistemas (Box Inferior)
* **RF04.1:** O sistema deve possuir uma área dedicada a "Cards" informativos que exibem estados simplificados.
* **RF04.2:** O sistema deve exibir o status do Trem de Pouso (ex: cruzamento da variável `LDG`).
* **RF04.3:** O sistema deve exibir o status do Motor (ex: Temperatura ITT, Fluxo de Combustível `FF`).
* **RF04.4:** O sistema deve exibir indicadores de Carga Dinâmica/Estrutural (ex: Força G no eixo Z - `NZ`), alertando visualmente para picos de aceleração.

### RF05: Sincronização de Contexto (Global)
* **RF05.1:** O sistema deve possuir um mecanismo de controle temporal (ex: slider ou cursor interativo no gráfico central).
* **RF05.2:** Ao mover o controle temporal, os RF02 (Atitude) e RF04 (Subsistemas) devem ser atualizados instantaneamente para refletir o valor exato no *timestamp* selecionado.

---

## 4. Requisitos de Interface do Usuário (UI)

* **UI01 - Layout em Grid:** A interface deve utilizar 100% da largura útil da tela (*wide layout*), dividida horizontalmente nos três blocos principais definidos nos RFs.
* **UI02 - Acessibilidade Visual:** O gráfico temporal deve possuir contraste adequado (fundo limpo/branco ou dark mode nativo) para facilitar a visualização das curvas de dados.
* **UI03 - Responsividade Otimizada:** Embora voltado para uso em monitores desktop de oficina ou bancada, os "cards" do Box Inferior devem quebrar a linha automaticamente se a janela for redimensionada.

---

## 5. Requisitos Não Funcionais (RNF)

* **RNF01 - Desempenho:** O sistema deve ser capaz de renderizar o gráfico temporal inicial para um arquivo com até 100.000 linhas em menos de 5 segundos.
* **RNF02 - Latência de Interação:** A atualização dos painéis secundários durante a navegação pela linha do tempo (scrubbing) deve ocorrer sem atrasos perceptíveis (latência inferior a 100ms).
* **RNF03 - Escalabilidade de Código:** A base de código Python deve ser modularizada para permitir a fácil inclusão de novos "Cards" de subsistemas no futuro, sem necessidade de reestruturação do layout base.