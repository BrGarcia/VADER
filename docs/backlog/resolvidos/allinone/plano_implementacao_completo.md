# Plano de Implementação: Modo COMPLETA (All-In-One)

Este documento detalha o passo a passo técnico para implementar o Dashboard Integrado (Vídeos + Telemetria) no ecossistema do VADER, aproveitando a stack atual (Python + Streamlit) e a capacidade de leitura de diretórios locais.

## 1. Módulo de Escaneamento de Diretório (Local File System)
**Objetivo:** Permitir que o Streamlit liste e acesse pastas locais contendo gigabytes de dados sem necessidade de upload via navegador.

*   **Tarefa 1.1:** Criar um utilitário em `src/utils/local_scanner.py`.
    *   Definir a constante `BASE_ANALYSIS_DIR = "Arquivos_para_analise/"`.
    *   Criar função `get_available_flights()`: Lista todas as subpastas (ex: `5941_130526`) dentro do diretório base.
    *   Criar função `scan_flight_folder(folder_name)`: Entra na pasta escolhida e retorna um dicionário com os caminhos absolutos dos arquivos encontrados:
        *   `vadr_csv_path`: Busca por `*.csv` na raiz ou subpasta VADR.
        *   `dtc_files_paths`: Busca por `TRIMM*.DMP` na subpasta DTC.
        *   `eicas_video_path`: Busca por vídeo (ex: `*.mp4`) na subpasta EICAS.
        *   `chvc_video_path`: Busca por vídeo na subpasta CHVC.

## 2. Atualização da Landing Page (Card 3)
**Objetivo:** Ativar o botão "Modo COMPLETA" usando o escaneamento local.

*   **Tarefa 2.1:** No arquivo `app.py` (dentro de `render_landing`), atualizar o Card 3.
    *   Substituir o estado "Em Desenvolvimento" por um `st.selectbox` que chama `get_available_flights()`.
    *   Adicionar botão "INICIAR COMPLETA".
    *   Ao clicar, executar `scan_flight_folder()`, salvar os caminhos encontrados no `st.session_state` e mudar o estado da aplicação (`st.session_state.modo_app = "completa"`).

## 3. Construção do Layout Base (Grid)
**Objetivo:** Criar a tela `render_completa()` no `app.py` que organizará os vídeos e os gráficos.

*   **Tarefa 3.1:** Desenhar o esqueleto do layout no Streamlit.
    *   **Topo:** Barra de ferramentas (Sincronização, Play/Pause global, Slider de Tempo Mestre).
    *   **Centro-Esquerda (Vídeos):** Duas colunas para os players de vídeo (EICAS e CHVC).
    *   **Centro-Direita (DTC):** Um pequeno painel de KPIs resumindo os disparos (reaproveitando os dados do `DtcParser`).
    *   **Base (Telemetria):** O gráfico gigante do Plotly (`TimelinePlotter`) expandido horizontalmente.

## 4. Integração de Mídia (HTML5 Video Player + JavaScript)
**Objetivo:** Exibir os vídeos locais e controlá-los programaticamente. O `st.video` nativo do Streamlit é limitado para sincronização fina via código, então precisaremos injetar um Player customizado.

*   **Tarefa 4.1:** Criar componente de vídeo em `src/ui/video_player.py`.
    *   Como os vídeos estão em uma pasta local, precisaremos expô-los usando o `st.components.v1.html` com a tag `<video>`.
    *   O Player do EICAS precisará de uma classe CSS para aplicar a rotação: `transform: rotate(90deg);`.
    *   **Desafio Técnico:** O Streamlit injeta HTML em iFrames. Para enviar comandos de "Play/Pause" e "Seek (pular para tempo X)" do Python para o iFrame do vídeo, usaremos parâmetros de Query ou variáveis de sessão bidirecionais (ex: Streamlit Component bidirecional ou recarga controlada de fragmentos).

## 5. Motor de Sincronização e Offsets
**Objetivo:** Implementar o Relógio Mestre e as correções de tempo.

*   **Tarefa 5.1:** Criar classe `SyncManager` em `src/core/sync.py`.
    *   Ler/Escrever arquivo `sync.json` na pasta do voo (contendo `{ "offset_eicas": +12.5, "offset_chvc": -4.2 }`).
*   **Tarefa 5.2:** Interface de Ajuste (Calibração).
    *   Adicionar um botão "⚙️ Calibrar Sincronia" no topo do dashboard.
    *   Abrir um modal/expander onde o usuário digita os segundos de atraso de cada vídeo em relação ao CSV.
*   **Tarefa 5.3:** Lógica de Reprodução.
    *   Quando o Slider de Tempo do VADR for movido para o segundo `T = 50`.
    *   O Python recalcula: `Tempo EICAS = 50 + offset_eicas`.
    *   Envia comando para o `<video>` pular para o tempo exato correspondente.

## Ordem de Execução Recomendada
1. **Passo 1 & 2:** Garantem que a estrutura consegue "enxergar" os arquivos locais sem bugar.
2. **Passo 3:** Montar o esqueleto visual (apenas retângulos vazios ou placeholders) para aprovação de design.
3. **Passo 4:** O coração do problema: fazer um vídeo tocar e rotacionar dentro do Streamlit.
4. **Passo 5:** Amarrar os vídeos ao relógio do Plotly (CSV).
