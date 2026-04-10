"""
app.py
Ponto de entrada do V.A.D.E.R.
Execute com: streamlit run app.py
"""

from __future__ import annotations

import os
import streamlit as st
import pandas as pd

from src.data_loader import DataLoader
from src.plots import TimelinePlotter
from src.ui_components import AttitudeBox, TimeController, EICASPanel, SubsystemCards

# -----------------------------------------------------------------------
# Configuração da Página
# -----------------------------------------------------------------------

st.set_page_config(
    page_title="V.A.D.E.R.",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

_LOADER = DataLoader()
_PLOTTER = TimelinePlotter()

# -----------------------------------------------------------------------
# Cache de ingestão
# -----------------------------------------------------------------------

@st.cache_data(show_spinner="Processando telemetria...")
def _ingest(file_bytes: bytes, filename: str) -> pd.DataFrame:
    raw_path = os.path.join(DataLoader.RAW_DIR, filename)
    os.makedirs(DataLoader.RAW_DIR, exist_ok=True)
    os.makedirs(DataLoader.PROCESSED_DIR, exist_ok=True)

    with open(raw_path, "wb") as fh:
        fh.write(file_bytes)

    return _LOADER.ingest(raw_path)

def _get_recent_files() -> list[str]:
    if not os.path.exists(DataLoader.RAW_DIR):
        return []
    files = [f for f in os.listdir(DataLoader.RAW_DIR) if f.endswith(".csv")]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(DataLoader.RAW_DIR, x)), reverse=True)
    return files


# -----------------------------------------------------------------------
# Menu Superior
# -----------------------------------------------------------------------

def render_top_menu(df_existing: pd.DataFrame | None = None) -> tuple[pd.DataFrame | None, str | None]:
    """Renderiza o menu superior horizontal e retorna (DataFrame, coluna_y)."""
    
    with st.expander("🛠️ CONFIGURAÇÕES E DADOS DE VOO", expanded=(df_existing is None)):
        col_file, col_var, col_info = st.columns([2, 1, 1])

        with col_file:
            st.markdown("**📂 Arquivo de Voo**")
            recent_files = _get_recent_files()
            selected_recent = None
            if recent_files:
                # Usamos st.session_state.get() para garantir persistência mas com chave fixa
                selected_recent = st.selectbox(
                    "Histórico",
                    options=["-- Novo Upload --"] + recent_files,
                    index=0,
                    label_visibility="collapsed",
                    key="top_menu_history_select"
                )

            uploaded = st.file_uploader(
                "Upload CSV",
                type=["csv"],
                label_visibility="collapsed",
                key="top_menu_csv_uploader"
            )

        df = df_existing
        filename = "Arquivo Carregado"

        if uploaded is not None:
            df = _ingest(uploaded.getvalue(), uploaded.name)
            filename = uploaded.name
        elif selected_recent and selected_recent != "-- Novo Upload --":
            raw_path = os.path.join(DataLoader.RAW_DIR, selected_recent)
            df = _LOADER.ingest(raw_path)
            filename = selected_recent

        if df is None:
            return None, None

        with col_var:
            st.markdown("**📊 Variável do Gráfico**")
            numeric_cols = _LOADER.get_numeric_columns(df)
            
            # Tenta recuperar a última variável selecionada ou usa default
            if "last_y_col" not in st.session_state:
                st.session_state.last_y_col = next(
                    (c for c in ("BALT", "MACH", "APA", "NZ") if c in numeric_cols),
                    numeric_cols[0] if numeric_cols else None
                )

            y_col = st.selectbox(
                "Eixo Y",
                options=numeric_cols,
                index=numeric_cols.index(st.session_state.last_y_col) if st.session_state.last_y_col in numeric_cols else 0,
                label_visibility="collapsed",
                key="top_menu_y_axis_select"
            )
            st.session_state.last_y_col = y_col

        with col_info:
            st.markdown("**ℹ️ Info do Voo**")
            n_rows = len(df)
            duration = df["TIME"].max() if "TIME" in df.columns else 0
            st.caption(f"📄 {filename}")
            st.caption(f"🔢 {n_rows:,} registros | ⏱ {duration:.1f} s")

    return df, y_col


# -----------------------------------------------------------------------
# Layout Principal
# -----------------------------------------------------------------------

def render_main(df: pd.DataFrame, y_col: str) -> None:
    """Monta o layout sincronizado."""

    controller    = TimeController(df)
    attitude_box  = AttitudeBox()
    subsys_cards  = SubsystemCards()
    fault_columns = _LOADER.get_fault_columns(df)

    time_idx = int(st.session_state.get(TimeController.SESSION_KEY, 0))
    snapshot = controller.get_snapshot(time_idx)

    # Monitor de Dados Compacto
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1: st.metric("TEMPO", f"{snapshot.get('TIME', 0):.2f}s")
    with m_col2: st.metric("TORQUE", f"{snapshot.get('Q', 0):.1f}%")
    with m_col3: st.metric("ITT", f"{snapshot.get('ITT', 0):.0f}°C")
    with m_col4: st.metric("MACH", f"{snapshot.get('MACH', 0):.3f}")

    # Box Superior
    st.markdown("#### ✈️ Atitude e Dados Críticos")
    attitude_box.render(snapshot)

    st.markdown("---")

    # Box Central (Gráfico)
    st.markdown(f"#### 📈 Análise Temporal — `{y_col}`")
    fig = _PLOTTER.plot(df, y_col)
    fig = _PLOTTER.add_phase_bands(fig, df)
    fig = _PLOTTER.add_fault_markers(fig, df, fault_columns, y_column=y_col)

    t_cursor = float(snapshot["TIME"]) if "TIME" in snapshot else 0
    fig.add_vline(
        x=t_cursor,
        line=dict(color="#FF4B4B", width=2, dash="dash"),
        annotation_text=f"  t={t_cursor:.2f}s",
        annotation_font=dict(color="#FF4B4B", size=11),
    )

    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True}, key=f"main_plot_{y_col}")

    # Slider de Tempo
    controller.render_slider()

    # Cards de Subsistemas
    st.markdown("---")
    st.markdown("#### 🔧 Subsistemas")
    subsys_cards.render_all(snapshot)


# -----------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------

def main() -> None:
    st.title("V.A.D.E.R. 🦅")
    st.caption("Visualizador Analítico de Dados de Engenharia e Rastreio — A-29")

    df_cached = st.session_state.get("current_df")
    df, y_col = render_top_menu(df_cached)

    if df is not None:
        st.session_state.current_df = df
        render_main(df, y_col)
    else:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                st.image("assets/a29_sideview.png", use_container_width=True)
            except Exception:
                pass
        st.info("📂 Configure o arquivo de voo no menu superior para iniciar a análise.")


if __name__ == "__main__":
    main()
