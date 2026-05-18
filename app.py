"""
app.py
Ponto de entrada principal do V.A.D.E.R.
Atua apenas como roteador (Controller) para as views separadas.
"""

from __future__ import annotations

import streamlit as st

# Importa as views modulares
from src.ui.views.landing import render_landing
from src.ui.views.vadr import render_main
from src.ui.views.dtc import render_dtc
from src.ui.views.completa import render_completa

# -----------------------------------------------------------------------
# Configuração da Página
# -----------------------------------------------------------------------

st.set_page_config(
    page_title="V.A.D.E.R.",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------
# Entrypoint (Roteador de Estado)
# -----------------------------------------------------------------------

def main() -> None:
    df_cached = st.session_state.get("current_df")
    modo = st.session_state.get("modo_app")

    if modo == "dtc":
        df_dtc = st.session_state.get("dtc_df")
        if df_dtc is not None:
            render_dtc(df_dtc)
        else:
            st.session_state.modo_app = None
            st.rerun()
            
    elif modo == "completa":
        render_completa()
        
    elif df_cached is not None:  # BUG-03: removida condição redundante
        # ── Página de Análise VADR ──
        st.session_state.modo_app = "vadr"  # BUG-08: define modo explicitamente
        render_main(df_cached)
        
    else:
        # ── Landing Page (Menu Inicial) ──
        render_landing()


if __name__ == "__main__":
    main()
