import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="V.A.D.E.R.", page_icon="🦅", layout="wide")

st.title("V.A.D.E.R. 🦅")
st.subheader("Visualizador Analítico de Dados de Engenharia e Rastreio")

st.info("Aplicação em desenvolvimento. O objetivo é a ingestão e visualização de telemetria de voo do A-29.")

# Sidebar para configurações
st.sidebar.header("Configurações")
st.sidebar.write("Em breve: Filtros e Seleção de Sensores")

# Placeholder para o futuro seletor de arquivos
uploaded_file = st.file_uploader("Selecione um arquivo CSV de telemetria", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.success(f"Arquivo carregado com sucesso! ({len(df)} linhas)")
        st.write("### Visualização prévia dos dados")
        st.dataframe(df.head(10))
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
else:
    st.warning("Aguardando carregamento de dados para iniciar a análise.")
