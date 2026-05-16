# Estruturação: Dashboard Integrado de Inspeção (All-In-One)

## 1. Visão Geral
O objetivo deste módulo é unificar a visualização de múltiplas fontes de dados de um voo (vídeos HUD, vídeos EICAS, dados binários DTC e dados tabulares VADR) em uma interface única. A ferramenta será voltada para a análise de inspetoria, permitindo a reprodução sincronizada de todos os eventos do voo.

## 2. Estrutura de Diretórios (Entrada de Dados)
A estrutura adotada facilitará a organização por voo/aeronave:
```text
VADER\Arquivos_para_analise\
└── <MATRICULA>_<DATA>\          # Ex: 5941_130526
    ├── CHVC\                    # Vídeos da câmera POV do piloto (HUD)
    ├── EICAS\                   # Vídeos da gravação de tela de equipamentos (MFD/EICAS)
    ├── DTC\                     # Arquivos de dump (TRIMM001.DMP, TRIMM002.DMP, etc.)
    └── VADR\                    # Arquivos CSV já tratados pelo VADER
```

## 3. Estrutura da Interface Visual (Layout Sugerido)
Como não posso visualizar diretamente o arquivo `ideia.bmp`, proponho um layout clássico e eficiente para dashboards de análise de voo:

*   **Cabeçalho (Header):**
    *   Identificação do Voo (Matrícula e Data).
    *   Controles Globais: `Play`, `Pause`, `Velocidade de Reprodução (1x, 2x, 0.5x)`.
    *   Status dos Dados: Indicadores (Verde/Vermelho) mostrando quais dados foram carregados (CHVC, EICAS, DTC, VADR).

*   **Área de Vídeos (Topo):**
    *   *Painel Esquerdo:* Player de Vídeo CHVC (Visão do HUD).
    *   *Painel Direito:* Player de Vídeo EICAS (Visão do Painel de Instrumentos).
        *   **Particularidade EICAS:** O vídeo original é salvo com uma rotação de 90 graus para a esquerda. O player deve aplicar uma correção automática (rotação de 90 graus para a direita / sentido horário) para exibição correta na interface.
    *   *Nota:* Se um dos vídeos não existir, o painel exibe um aviso "Vídeo Indisponível" sem quebrar o layout.

*   **Área de Gráficos e Telemetria (Centro/Baixo):**
    *   Gráficos dinâmicos (ex: Altitude, Velocidade, N1, N2, etc.) lidos dos CSVs do VADR/DTC.
    *   Uma **Linha do Tempo Global (Timeline)** interativa que controla os vídeos e um "cursor" (linha vertical) que se move pelos gráficos simultaneamente.

*   **Painel de Sincronização (Lateral ou Modal):**
    *   Controles individuais de *offset* (atraso/adiantamento em segundos) para cada fonte (CHVC, EICAS, DTC) em relação ao tempo mestre (geralmente o CSV do VADR dita o "tempo zero").

## 4. Lógica de Resiliência (Funcionamento Independente)
O sistema deve ser construído com uma arquitetura baseada em **Módulos/Componentes Opcionais**:
1.  **Core (Motor de Tempo):** Um gerenciador central de estado de tempo. Ele dita qual é o "segundo atual" da reprodução.
2.  **Módulos de Ingestão:** Ao selecionar a pasta `5941_130526`, o sistema verifica a existência de arquivos nas 4 subpastas.
3.  **Fallback (Suporte a Qualquer Combinação):** O sistema será desenhado para carregar e reproduzir **qualquer combinação de arquivos** disponível na pasta, sem dependências obrigatórias entre eles.
    *   **Apenas um tipo de dado:** Se existir apenas os arquivos de um tipo (ex: apenas vídeos do EICAS, ou apenas o TRIMM, ou apenas o CSV do VADR), o módulo correspondente será carregado e funcionará de forma isolada e autossuficiente.
    *   **Múltiplos parciais:** Se existirem fontes variadas (ex: apenas TRIMM e EICAS), somente esses módulos serão exibidos e a sincronia funcionará entre eles.
    *   **Ausência de dados:** Para cada fonte não encontrada na pasta, o respectivo painel será ocultado ou exibirá um alerta ("Sem dados"), sem travar ou impedir a reprodução do restante. Se a pasta estiver 100% vazia, exibirá uma mensagem de erro como "Nenhum arquivo encontrado na pasta."

## 5. Estratégia de Sincronização
Como as gravações iniciam em momentos distintos, é impossível dar "Play" e tudo estar sincronizado magicamente na primeira vez sem um marco (timestamp).
**Solução Proposta:**
1.  **Tempo Mestre (Master Clock):** Os dados do CSV (VADR) possuem uma coluna de tempo exata (ex: T+0, T+1, T+2). O CSV será o nosso Relógio Mestre.
2.  **Ajuste Manual Visual (Offsets):**
    *   O usuário olha para um evento claro no CSV (ex: Rotação do motor sai de 0, ou *Weight on Wheels* muda de estado).
    *   O usuário pausa a linha do tempo do CSV nesse exato evento.
    *   Na interface, haverá botões para "Deslizar" o vídeo do CHVC e do EICAS para frente e para trás até que a imagem corresponda visualmente ao evento dos gráficos.
    *   Ao achar o ponto, o usuário clica em "Travar Sincronia". O sistema salva esse *offset* (ex: Vídeo 1 começou +12.5s depois do CSV) em um arquivo de configuração (ex: `sync.json` dentro da pasta `5941_130526`).
3.  **Reprodução Sincronizada:** Quando o usuário der Play no Relógio Mestre, o sistema manda o comando de play para os vídeos aplicando o *offset* salvo.

## 6. Reaproveitamento e Modularidade do Código (Stack Atual)
O projeto consolidou-se utilizando **Python + Streamlit**. Com isso, o ecossistema de ingestão de dados foi refatorado para funcionar como módulos independentes:
*   **VADR (`src/data/data_loader.py`):** Lógica de ingestão clássica de CSV, extraindo metadados e persistindo cache colunar (Parquet).
*   **DTC (`src/data/dtc_parser.py`):** Lógica de ingestão e consolidação de arquivos binários de falha (`TRIMM.DMP`), já adaptada para calcular *thresholds* e flags de atuação não comandada.
O Frontend deve apenas consultar essas classes; ele não deve processar regras de negócio.

## 7. Estratégia da Página Inicial (Landing Page)
A Landing Page atua como um **Hub de Módulos (Cards)**.
*   **Card 1: Modo VADR (Atual):** Operação via *Upload* em memória ou seleção de histórico de CSV. Mantém a análise focada em gráficos.
*   **Card 2: Modo DTC (Ativo):** Operação via *Upload* em memória de múltiplos arquivos `.DMP`. Exibe o painel focado em sumarização de falhas matemáticas nos atuadores.
*   **Card 3: Modo COMPLETO (Inspetoria/All-In-One):** 
    *   Como vídeos de voo são extremamente grandes, **não usaremos upload via navegador**.
    *   A interface fará um *Scan Local* na pasta raiz predefinida (ex: `VADER/Arquivos_para_analise/`).
    *   O usuário selecionará a pasta do voo (ex: `5941_130526`) através de um Dropdown.
    *   O sistema inspecionará silenciosamente as subpastas (VADR, DTC, EICAS, CHVC), acionará os *parsers* respectivos para dados suportados, e repassará os caminhos absolutos dos vídeos para o renderizador de mídia.

## Próximos Passos (Plano de Implementação)
O foco agora se desloca 100% para a criação do Layout Sincronizado do "Modo COMPLETA", detalhado no `plano_implementacao_completo.md`.
