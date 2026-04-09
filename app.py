"""
app.py
Ponto de entrada do V.A.D.E.R.
Execute com: streamlit run app.py
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from src.data_loader import DataLoader
from src.ui_components import AttitudeBox, EICASPanel, SubsystemCards, TimeController

# -----------------------------------------------------------------------
# Configuração da Página
# -----------------------------------------------------------------------

st.set_page_config(
    page_title="V.A.D.E.R.",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------
# Sidebar: Ingestão de Arquivo
# -----------------------------------------------------------------------

def render_sidebar() -> pd.DataFrame | None:
    """Renderiza a sidebar com o seletor de arquivo CSV e retorna o DataFrame carregado."""
    ...


# -----------------------------------------------------------------------
# Layout Principal
# -----------------------------------------------------------------------

def render_main(df: pd.DataFrame) -> None:
    """Monta o layout de três boxes e sincroniza todos via TimeController.

    Estrutura:
        Box Superior  → AttitudeBox (horizonte artificial + altitude + velocidade)
        Box Central   → Gráfico temporal interativo (TimelinePlotter)
        Box Inferior  → SubsystemCards + EICASPanel
    """
    ...


# -----------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------

def main() -> None:
    st.title("V.A.D.E.R. 🦅")
    st.caption("Visualizador Analítico de Dados de Engenharia e Rastreio — A-29")

    df = render_sidebar()

    if df is None:
        st.info("Carregue um arquivo CSV do VADR na barra lateral para iniciar.")
        st.image("assets/a29_sideview.png", use_column_width=True)
        return

    render_main(df)


if __name__ == "__main__":
    main()
