# Decisões de Engenharia (Decisions / ADR)

## DEC-001: Arquitetura Orientada a Interface com Streamlit
- **Contexto:** A análise de telemetria necessitava inicialmente da manipulação direta das curvas através do pacote Pandas/Matplotlib/Plotly no Google Colab ou Jupyter. Essa visão afastava o operador de manutenção que é focado na leitura do painel.
- **Decisão:** Optou-se por construir uma interface completa unificada via `Streamlit`.
- **Benefícios:** Acelera o desenvolvimento, integra diretamente script python com Web, evita setups complexos no Backend.

## DEC-002: Serialização em Apache Parquet
- **Contexto:** Arquivos VADR demoram de 3 a 5 segundos para serem ingeridos liminarmente pelo `pd.read_csv`, além de exigir rotinas de casting constante. Missões muito longas travavam a interface.
- **Decisão:** Criação do cache `.parquet`. A primeira ingestão traduz, tipifica e faz *Forward-fill* (propagação) de subsistemas de baixa resolução diretamente persistindo na pasta `data/processed/`. Das leituras subsequentes, carrega instantaneamente (<0.1s).
- **Benefícios:** Velocidade de carga e uso eficiente de compressão snnapy.

## DEC-003: Renderização Vetorial Geométricas de Instrumentos
- **Contexto:** Streamlit não possui mostradores robustos estilo Aviação, limitando-se aos charts tradicionais.
- **Decisão:** O VADER usa `Plotly` para simular displays vetorizados através do backend WebGL/SVG. Todo painel EICAS é, por essência, uma figura estática Plotly atualizada via callbacks do Streamlit.

## DEC-004: State Management e Reactividade Temporal Global
- **Contexto:** Todas as caixas e gauges devem observar o mesmo momento `T` temporal sem renderizar forçosamente toda a base.
- **Decisão:** Gerou-se uma classe base (`TimeController`) que injeta a flag temporal da posição em `st.session_state`. Todo componente assina a leitura a partir da chamada de `.get_snapshot()`, passando a linha/row daquele exato ponto. O slider funciona de base como um Index universal.
