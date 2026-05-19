from __future__ import annotations

import copy
import html
import os
import streamlit as st
import pandas as pd
from src.data.data_loader import DataLoader
from src.ui.plots import TimelinePlotter
from src.ui.components import AttitudeBox, TimeController, SubsystemCards
from src.ui.components.flight_map import FlightMap
from src.ui.views.landing import _get_recent_files, _LOADER

_PLOTTER = TimelinePlotter()
_FLIGHT_MAP = FlightMap()  # IMP-07: instanciado uma vez no nível de módulo


# -----------------------------------------------------------------------
# A.3 — Figura base cacheada (sem cursor)
# -----------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def build_base_figure(
    df: pd.DataFrame,
    y_cols: tuple[str, ...],
    fault_columns: tuple[str, ...],
    exceedance_tuple: tuple[str, str, float] | None = None,
) -> object:
    """Constrói e retorna a figura Plotly base sem o cursor temporal.

    A.3 — Cacheada por (df, y_cols, fault_columns). Traces, faixas de fase e
    marcadores de falha não mudam enquanto o usuário move o slider — apenas
    o cursor muda. Separar aqui evita rebuild Python + serialização a cada tick.
    """
    exc_config = None
    if exceedance_tuple:
        exc_config = {
            "var": exceedance_tuple[0],
            "op": exceedance_tuple[1],
            "val": exceedance_tuple[2]
        }
    fig = _PLOTTER.plot(df, list(y_cols), exceedance_config=exc_config)
    fig = _PLOTTER.add_phase_bands(fig, df)
    fig = _PLOTTER.add_fault_markers(fig, df, list(fault_columns), y_column=list(y_cols))
    return fig

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
                        # A.6 — respeita o modo escolhido na landing page
                        mode = st.session_state.get("analysis_mode", "complete")
                        new_df = _LOADER.ingest(raw_path, analysis_mode=mode)
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

@st.fragment
def render_main(df: pd.DataFrame, show_metadata: bool = True) -> str | None:
    """Monta o layout sincronizado de análise. Retorna y_col selecionado."""

    controller    = TimeController(df)
    attitude_box  = AttitudeBox()
    subsys_cards  = SubsystemCards()
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

    # ── Configuração de Excedências (Highlight) ──
    # Lemos os valores salvos no session_state para construir a exceedance_tuple antes do gráfico
    exc_var = st.session_state.get("exc_var_select", "Nenhuma")
    exc_op = st.session_state.get("exc_op_select", ">")

    # Atualiza valor padrão do limite caso a variável tenha mudado
    last_exc_var = st.session_state.get("last_exc_var_state", "Nenhuma")
    if exc_var != last_exc_var:
        st.session_state.last_exc_var_state = exc_var
        default_val = 0.0
        if exc_var != "Nenhuma" and exc_var in df.columns:
            try:
                default_val = float(df[exc_var].mean())
            except Exception:
                pass
        st.session_state.exc_val_input = default_val

    exc_val = st.session_state.get("exc_val_input", 0.0)

    exceedance_tuple = None
    if exc_var != "Nenhuma" and exc_var in y_cols:
        exceedance_tuple = (exc_var, exc_op, float(exc_val))

    label_vars = " · ".join(f"`{c}`" for c in y_cols)
    titulo_placeholder.markdown(f"#### 📈 Análise Temporal — {label_vars}")

    # A.3 — obtém a figura base cacheada (sem cursor)
    base_fig = build_base_figure(df, tuple(y_cols), tuple(fault_columns), exceedance_tuple)

    # B.3 — Mantém o estado de zoom (X-axis range) entre reruns usando uirevision baseada no arquivo
    filename = st.session_state.get("current_filename", "vader_file")
    base_fig.update_layout(uirevision=filename)

    # ── Renderização Centralizada (Gráfico) ──
    # Renderizamos em largura total correspondendo aos cards e ao restante da página
    st.plotly_chart(base_fig, width="stretch", config={"scrollZoom": True}, key=f"main_plot_{y_col}")

    # ── Configuração de Excedências (Highlight) ──
    with st.expander("⚠️ Destacar Excedências (Exceedance Highlight)"):
        col_exc1, col_exc2, col_exc3 = st.columns([2, 1, 1], gap="small")
        with col_exc1:
            st.selectbox(
                "Variável",
                options=["Nenhuma"] + y_cols,
                key="exc_var_select"
            )
        with col_exc2:
            st.selectbox(
                "Operação",
                options=[">", "<", ">=", "<=", "=="],
                key="exc_op_select"
            )
        with col_exc3:
            # Semente o valor padrão apenas se ainda não estiver no session_state
            if "exc_val_input" not in st.session_state:
                default_val = 0.0
                if exc_var != "Nenhuma" and exc_var in df.columns:
                    try:
                        default_val = float(df[exc_var].mean())
                    except Exception:
                        pass
                st.session_state["exc_val_input"] = default_val
            st.number_input(
                "Valor Limite",
                format="%.4f",
                key="exc_val_input"
            )

    st.markdown("---")

    # Atitude e Dados Críticos
    st.markdown("#### ✈️ Atitude e Dados Críticos")
    attitude_box.render(snapshot, fault_columns)

    # Cards de Subsistemas
    st.markdown("#### 🔧 Subsistemas")
    subsys_cards.render_all(snapshot)

    # Rastreio Geográfico
    st.markdown("#### 🗺️ Rastreio Geográfico")
    with st.container(border=True):
        _FLIGHT_MAP.render(df, snapshot)  # IMP-07: usa instância de módulo

    # Painel inferior (configurações + nova análise)
    render_bottom_panel(df)

    return y_col
