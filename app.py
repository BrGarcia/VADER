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
    """Renderiza o menu superior horizontal ultracompacto."""
    
    with st.container(border=True):
        # Título em linha única e menor
        st.markdown("<p style='font-weight: bold; margin-bottom: 0px; font-size: 0.8rem; text-align: center;'>🛠️ CONFIGURAÇÕES E DADOS DE VOO</p>", unsafe_allow_html=True)
        
        col_file, col_var, col_info = st.columns([1.5, 1, 1], gap="small")

        with col_file:
            recent_files = _get_recent_files()
            if recent_files:
                st.selectbox(
                    "Histórico",
                    options=["-- Histórico --"] + recent_files,
                    index=0,
                    label_visibility="collapsed",
                    key="top_menu_history_select"
                )
            
            st.file_uploader(
                "Upload",
                type=["csv"],
                label_visibility="collapsed",
                key="top_menu_csv_uploader"
            )

        # Lógica de carga de dados (simplificada para manter o fluxo)
        uploaded = st.session_state.get("top_menu_csv_uploader")
        selected_recent = st.session_state.get("top_menu_history_select")
        
        df = df_existing
        filename = "Arquivo Carregado"

        if uploaded is not None:
            df = _ingest(uploaded.getvalue(), uploaded.name)
            filename = uploaded.name
        elif selected_recent and selected_recent != "-- Histórico --":
            raw_path = os.path.join(DataLoader.RAW_DIR, selected_recent)
            df = _LOADER.ingest(raw_path)
            filename = selected_recent

        if df is None:
            return None, None

        with col_var:
            st.markdown("<p style='font-size: 0.75rem; font-weight: bold; margin-bottom: -15px; text-align: center;'>📊 VARIÁVEL</p>", unsafe_allow_html=True)
            numeric_cols = _LOADER.get_numeric_columns(df)
            
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
            st.markdown("<p style='font-size: 0.75rem; font-weight: bold; margin-bottom: -10px; text-align: center;'>ℹ️ INFO</p>", unsafe_allow_html=True)
            n_rows = len(df)
            duration = df["TIME"].max() if "TIME" in df.columns else 0
            st.markdown(f"<p style='font-size: 0.7rem; margin-bottom: 0px; text-align: center;'>📄 {filename[:20]}...</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 0.7rem; text-align: center;'>🔢 {n_rows:,} registros | ⏱ {duration:.1f}s</p>", unsafe_allow_html=True)

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

    # --- NOVO: Cabeçalho de Dados da Aeronave ---
    metadata = df.attrs.get("metadata", {})
    if metadata:
        with st.container(border=True):
            st.markdown("<p style='font-weight: bold; margin-bottom: 5px; font-size: 0.85rem; text-align: center;'>✈️ DADOS DA AERONAVE</p>", unsafe_allow_html=True)
            cols_meta = st.columns(len(metadata) if len(metadata) > 0 else 1)
            for i, (key, val) in enumerate(metadata.items()):
                with cols_meta[i % len(cols_meta)]:
                    st.markdown(f"<p style='font-size: 0.75rem; text-align: center;'><span style='color: #888;'>{key}:</span> <br><b>{val}</b></p>", unsafe_allow_html=True)

    time_idx = int(st.session_state.get(TimeController.SESSION_KEY, 0))
    snapshot = controller.get_snapshot(time_idx)

    # Box Superior
    st.markdown("#### ✈️ Atitude e Dados Críticos")
    attitude_box.render(snapshot, fault_columns)

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

    # --- CONFIGURAÇÕES MOVIDAS PARA O FINAL ---
    st.markdown("---")
    render_top_menu(df)


# -----------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------

def main() -> None:
    # Cabeçalho Centralizado
    _, col_mid, _ = st.columns([2, 1, 2])
    with col_mid:
        st.image("assets/a29_sideview.png", use_container_width=True)
        st.markdown("<h1 style='text-align: center; margin-top: -20px;'>V.A.D.E.R.</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-style: italic; color: #888; font-size: 0.9em;'>Visualizador Analítico de Dados de Engenharia e Rastreio — A-29</p>", unsafe_allow_html=True)

    df_cached = st.session_state.get("current_df")
    
    if df_cached is not None:
        # Se já temos dados, renderizamos o conteúdo principal (que agora inclui o menu no fim)
        # Precisamos descobrir qual a coluna Y atual.
        y_col = st.session_state.get("last_y_col", "BALT")
        render_main(df_cached, y_col)
    else:
        # Se não há dados, mostramos o menu no topo para permitir o primeiro upload
        df, y_col = render_top_menu(None)
        if df is not None:
            st.session_state.current_df = df
            st.rerun()
        st.info("📂 Configure o arquivo de voo no menu acima para iniciar a análise.")


if __name__ == "__main__":
    main()
