from __future__ import annotations

import html
import os
import streamlit as st
import pandas as pd
from src.data.data_loader import DataLoader
from src.ui.plots import TimelinePlotter
from src.ui.components import AttitudeBox, TimeController
from src.ui.views.landing import _get_recent_files, _LOADER

_PLOTTER = TimelinePlotter()

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
            fname_safe = html.escape(fname[:24])  # SEC-01: sanitiza contra XSS
            st.markdown(f"<p style='font-size: 0.7rem; margin-bottom: 0px; text-align: center;'>📄 {fname_safe}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size: 0.7rem; text-align: center;'>🔢 {n_rows:,} registros | ⏱ {duration / 60:.2f} min</p>", unsafe_allow_html=True)

        # ── Botão Nova Análise ──
        with col_btn:
            st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
            if st.button("🔄  NOVA ANÁLISE", key="btn_nova_analise", use_container_width=True):
                # Limpa o estado e retorna à landing page
                for key in ["current_df", "current_filename", "last_y_col",
                             TimeController.SESSION_KEY]:
                    st.session_state.pop(key, None)
                st.rerun()

def render_main(df: pd.DataFrame, show_metadata: bool = True) -> str | None:
    """Monta o layout sincronizado de análise. Retorna y_col selecionado."""

    controller    = TimeController(df)
    attitude_box  = AttitudeBox()
    fault_columns = _LOADER.get_fault_columns(df)

    # Cabeçalho de Dados da Aeronave
    if show_metadata:
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

    # ── Análise Temporal: título + seletor de variáveis inline ──
    numeric_cols = _LOADER.get_numeric_columns(df)

    # Padrão inicial: primeira variável relevante disponível
    if "last_y_cols" not in st.session_state:
        default = next(
            (c for c in ("BALT", "MACH", "APA", "NZ") if c in numeric_cols),
            numeric_cols[:1]
        )
        st.session_state.last_y_cols = [default] if isinstance(default, str) else default

    col_titulo, col_sel = st.columns([2, 1], gap="small")
    with col_titulo:
        titulo_placeholder = st.empty()
    with col_sel:
        y_cols = st.multiselect(
            "Variáveis",
            options=numeric_cols,
            default=[c for c in st.session_state.last_y_cols if c in numeric_cols] or numeric_cols[:1],
            label_visibility="collapsed",
            placeholder="Selecione as variáveis...",
            key="main_y_axis_select"
        )
        # Garante ao menos uma variável selecionada
        if not y_cols:
            y_cols = st.session_state.last_y_cols or numeric_cols[:1]
        st.session_state.last_y_cols = y_cols
        # Compatibilidade com código que usa last_y_col (singular)
        y_col = y_cols[0] if y_cols else None
        st.session_state.last_y_col = y_col

    label_vars = " · ".join(f"`{c}`" for c in y_cols)
    titulo_placeholder.markdown(f"#### 📈 Análise Temporal — {label_vars}")

    fig = _PLOTTER.plot(df, y_cols)
    fig = _PLOTTER.add_phase_bands(fig, df)
    fig = _PLOTTER.add_fault_markers(fig, df, fault_columns, y_column=y_cols)


    t_cursor = float(snapshot["TIME"]) if "TIME" in snapshot else 0
    fig.add_vline(
        x=t_cursor / 60,
        line=dict(color="#FF4B4B", width=2, dash="dash"),
        annotation_text=f"  t={t_cursor / 60:.2f} min",
        annotation_font=dict(color="#FF4B4B", size=11),
    )

    # ── Renderização Centralizada (Gráfico e Controle) ──
    # Diminuímos a largura horizontal do gráfico e da barra para forçá-los ao mesmo tamanho exato
    _, col_centro, _ = st.columns([0.05, 0.9, 0.05])
    
    with col_centro:
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True}, key=f"main_plot_{y_col}")
        # Slider de Tempo logo abaixo do gráfico
        controller.render_slider()

    st.markdown("---")

    # Atitude e Dados Críticos
    st.markdown("#### ✈️ Atitude e Dados Críticos")
    attitude_box.render(snapshot, fault_columns)

    # Cards de Subsistemas e Rastreio Geográfico foram removidos deliberadamente
    # em commits anteriores (simplificação da UI); flight_map.py e o antigo
    # SubsystemCards ficam arquivados/inativos ate uma reativacao futura.

    # Painel inferior (configurações + nova análise)
    render_bottom_panel(df)

    return y_col
