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
# Landing Page
# -----------------------------------------------------------------------

def render_landing() -> None:
    """Landing page: cabeçalho + box de upload + botão ENVIAR."""

    recent_files = _get_recent_files()

    # ── Cabeçalho centralizado ──
    _, col_mid, _ = st.columns([2, 1, 2])
    with col_mid:
        st.image("assets/a29_sideview.png", use_container_width=True)
        st.markdown("<h1 style='text-align: center; margin-top: -20px;'>V.A.D.E.R.</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-style: italic; color: #888; font-size: 0.9em;'>Visualizador Analítico de Dados de Engenharia e Rastreio — A-29</p>", unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # ── Box de configuração centralizado ──
    _l, _box, _r = st.columns([1, 2, 1])
    with _box:
        with st.container(border=True):
            st.markdown("<p style='font-weight: bold; margin-bottom: 8px; font-size: 0.85rem; text-align: center;'>🛠️ CONFIGURAÇÕES E DADOS DE VOO</p>", unsafe_allow_html=True)

            # Histórico
            if recent_files:
                st.markdown("<p style='font-size: 0.72rem; font-weight: bold; margin-bottom: 0px; text-align: center;'>📁 HISTÓRICO</p>", unsafe_allow_html=True)
                st.selectbox(
                    "Histórico",
                    options=["-- Selecione um voo recente --"] + recent_files,
                    index=0,
                    label_visibility="collapsed",
                    key="landing_history_select"
                )

            # Upload
            st.markdown("<p style='font-size: 0.72rem; font-weight: bold; margin-bottom: 0px; text-align: center;'>⬆️ UPLOAD CSV</p>", unsafe_allow_html=True)
            st.file_uploader(
                "Upload CSV",
                type=["csv"],
                label_visibility="collapsed",
                key="landing_csv_uploader"
            )

            # Feedback de seleção
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            uploaded = st.session_state.get("landing_csv_uploader")
            selected_recent = st.session_state.get("landing_history_select")
            arquivo_pronto = uploaded is not None or (
                selected_recent and selected_recent != "-- Selecione um voo recente --"
            )

            if arquivo_pronto:
                nome = uploaded.name if uploaded else selected_recent
                st.markdown(f"<p style='font-size: 0.72rem; text-align: center; color: #4CAF50; margin-top: 2px;'>✅ {nome}</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='font-size: 0.72rem; text-align: center; color: #888; margin-top: 2px;'>Selecione um arquivo CSV para habilitar o envio.</p>", unsafe_allow_html=True)

            # ── Botão ENVIAR ──
            _, btn_col, _ = st.columns([1, 2, 1])
            with btn_col:
                enviar = st.button(
                    "▶  ENVIAR",
                    type="primary",
                    use_container_width=True,
                    key="landing_submit_btn",
                    disabled=not arquivo_pronto,
                )

            # ── Processa somente ao clicar ENVIAR ──
            if enviar:
                if uploaded is not None:
                    new_df = _ingest(uploaded.getvalue(), uploaded.name)
                    if new_df is not None:
                        st.session_state.current_df = new_df
                        st.session_state.current_filename = uploaded.name
                        st.rerun()
                    else:
                        st.error("❌ Falha ao processar o arquivo CSV.")
                elif selected_recent and selected_recent != "-- Selecione um voo recente --":
                    raw_path = os.path.join(DataLoader.RAW_DIR, selected_recent)
                    new_df = _LOADER.ingest(raw_path)
                    if new_df is not None:
                        st.session_state.current_df = new_df
                        st.session_state.current_filename = selected_recent
                        st.rerun()
                    else:
                        st.error("❌ Falha ao carregar o arquivo do histórico.")


# -----------------------------------------------------------------------
# Menu compacto (página de análise)
# -----------------------------------------------------------------------

def render_bottom_panel(df: pd.DataFrame) -> None:
    """Painel inferior: troca de arquivo, info e botão Nova Análise."""

    recent_files = _get_recent_files()

    st.markdown("---")
    with st.container(border=True):
        st.markdown("<p style='font-weight: bold; margin-bottom: 4px; font-size: 0.8rem; text-align: center;'>🛠️ CONFIGURAÇÕES E DADOS DE VOO</p>", unsafe_allow_html=True)

        col_file, col_info, col_btn = st.columns([2, 1.5, 1], gap="small")

        # ── Troca rápida de arquivo ──
        with col_file:
            _l, _mid, _r = st.columns([0.05, 0.9, 0.05])
            with _mid:
                opcoes = ["── Arquivo atual ──"] + (recent_files if recent_files else [])
                sel = st.selectbox(
                    "Trocar arquivo",
                    options=opcoes,
                    index=0,
                    label_visibility="collapsed",
                    key="analysis_history_select"
                )
                if sel and sel != "── Arquivo atual ──":
                    if st.button("▶  Carregar", key="analysis_load_btn", use_container_width=True):
                        raw_path = os.path.join(DataLoader.RAW_DIR, sel)
                        new_df = _LOADER.ingest(raw_path)
                        if new_df is not None:
                            st.session_state.current_df = new_df
                            st.session_state.current_filename = sel
                            st.rerun()

        # ── Info do arquivo atual ──
        with col_info:
            st.markdown("<p style='font-size: 0.75rem; font-weight: bold; margin-bottom: -10px; text-align: center;'>ℹ️ INFO</p>", unsafe_allow_html=True)
            n_rows = len(df)
            duration = df["TIME"].max() if "TIME" in df.columns else 0
            fname = st.session_state.get("current_filename", "arquivo")
            st.markdown(f"<p style='font-size: 0.7rem; margin-bottom: 0px; text-align: center;'>📄 {fname[:24]}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 0.7rem; text-align: center;'>🔢 {n_rows:,} registros | ⏱ {duration:.1f}s</p>", unsafe_allow_html=True)

        # ── Botão Nova Análise ──
        with col_btn:
            st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
            if st.button("🔄  NOVA ANÁLISE", key="btn_nova_analise", use_container_width=True):
                # Limpa o estado e retorna à landing page
                for key in ["current_df", "current_filename", "last_y_col",
                             TimeController.SESSION_KEY]:
                    st.session_state.pop(key, None)
                st.rerun()


# -----------------------------------------------------------------------
# Layout Principal (Análise)
# -----------------------------------------------------------------------

def render_main(df: pd.DataFrame) -> str | None:
    """Monta o layout sincronizado de análise. Retorna y_col selecionado."""

    controller    = TimeController(df)
    attitude_box  = AttitudeBox()
    subsys_cards  = SubsystemCards()
    fault_columns = _LOADER.get_fault_columns(df)

    # Cabeçalho de Dados da Aeronave
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

    # Atitude e Dados Críticos
    st.markdown("#### ✈️ Atitude e Dados Críticos")
    attitude_box.render(snapshot, fault_columns)

    st.markdown("---")

    # ── Análise Temporal: título + seletor de variável inline ──
    numeric_cols = _LOADER.get_numeric_columns(df)
    if "last_y_col" not in st.session_state:
        st.session_state.last_y_col = next(
            (c for c in ("BALT", "MACH", "APA", "NZ") if c in numeric_cols),
            numeric_cols[0] if numeric_cols else None
        )

    col_titulo, col_sel = st.columns([3, 1], gap="small")
    with col_titulo:
        # placeholder — será preenchido após definir y_col
        titulo_placeholder = st.empty()
    with col_sel:
        y_col = st.selectbox(
            "Variável",
            options=numeric_cols,
            index=numeric_cols.index(st.session_state.last_y_col) if st.session_state.last_y_col in numeric_cols else 0,
            label_visibility="collapsed",
            key="main_y_axis_select"
        )
        st.session_state.last_y_col = y_col

    titulo_placeholder.markdown(f"#### 📈 Análise Temporal — `{y_col}`")

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
    st.markdown("#### 🔧 Subsistemas")
    subsys_cards.render_all(snapshot)

    # Painel inferior (configurações + nova análise)
    render_bottom_panel(df)

    return y_col


# -----------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------

def main() -> None:
    df_cached = st.session_state.get("current_df")

    if df_cached is not None:
        # ── Página de Análise ──
        render_main(df_cached)
    else:
        # ── Landing Page ──
        render_landing()


if __name__ == "__main__":
    main()
