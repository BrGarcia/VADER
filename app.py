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
    initial_sidebar_state="expanded",
)

_LOADER = DataLoader()
_PLOTTER = TimelinePlotter()

# -----------------------------------------------------------------------
# Cache de ingestão (só reprocessa se o conteúdo do arquivo mudar)
# -----------------------------------------------------------------------

@st.cache_data(show_spinner="Processando telemetria...")
def _ingest(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Salva o upload em data/raw/ e aciona o DataLoader."""
    raw_path = os.path.join(DataLoader.RAW_DIR, filename)
    os.makedirs(DataLoader.RAW_DIR, exist_ok=True)
    os.makedirs(DataLoader.PROCESSED_DIR, exist_ok=True)

    with open(raw_path, "wb") as fh:
        fh.write(file_bytes)

    return _LOADER.ingest(raw_path)

def _get_recent_files() -> list[str]:
    """Lista arquivos CSV disponíveis em data/raw/ ordenados por data de modificação."""
    if not os.path.exists(DataLoader.RAW_DIR):
        return []
    files = [f for f in os.listdir(DataLoader.RAW_DIR) if f.endswith(".csv")]
    # Ordena por data de modificação (mais recentes primeiro)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(DataLoader.RAW_DIR, x)), reverse=True)
    return files


# -----------------------------------------------------------------------
# Sidebar: Ingestão + Seleção de Variável
# -----------------------------------------------------------------------

def render_sidebar() -> tuple[pd.DataFrame | None, str | None]:
    """Renderiza a sidebar e retorna (DataFrame, coluna_y) ou (None, None)."""
    try:
        st.sidebar.image("assets/a29_sideview_RL.png", use_container_width=True)
    except Exception:
        pass

    st.sidebar.markdown("---")
    st.sidebar.header("📂 Arquivo de Voo")

    # Histórico de Arquivos
    recent_files = _get_recent_files()
    selected_recent = None
    if recent_files:
        st.sidebar.subheader("Últimas Análises")
        # Usamos um selectbox para economizar espaço se houver muitos arquivos
        selected_recent = st.sidebar.selectbox(
            "Selecionar do histórico",
            options=["-- Novo Upload --"] + recent_files,
            index=0,
            help="Escolha um arquivo previamente carregado ou faça upload de um novo abaixo."
        )

    uploaded = st.sidebar.file_uploader(
        "Selecione o CSV do VADR",
        type=["csv"],
        help="Arquivo exportado pelo Ground Station VADR (.csv)",
    )

    df = None
    filename = None

    if uploaded is not None:
        df = _ingest(uploaded.getvalue(), uploaded.name)
        filename = uploaded.name
    elif selected_recent and selected_recent != "-- Novo Upload --":
        raw_path = os.path.join(DataLoader.RAW_DIR, selected_recent)
        df = _LOADER.ingest(raw_path)
        filename = selected_recent

    if df is None:
        return None, None

    n_rows = len(df)
    duration = df["TIME"].max() if "TIME" in df.columns else 0
    st.sidebar.success(
        f"✓ **{filename}**  \n"
        f"📊 {n_rows:,} registros  \n"
        f"⏱ Duração: {duration:.1f} s"
    )

    # Seleção da variável para o eixo Y
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Variável do Gráfico")

    numeric_cols = _LOADER.get_numeric_columns(df)
    
    # DEBUG: Mostrar colunas do motor se encontradas
    engine_vars = ["Q", "ITT", "NG", "NP", "FF", "OT", "OP"]
    found_vars = [v for v in engine_vars if v in df.columns]
    if found_vars:
        st.sidebar.info(f"Detectadas: {', '.join(found_vars)}")
    else:
        st.sidebar.error("⚠️ Colunas do motor NÃO detectadas!")
        # Mostra as primeiras 10 colunas para ajudar no diagnóstico
        st.sidebar.write(f"Primeiras colunas: {list(df.columns[:10])}")

    if not numeric_cols:
        st.sidebar.warning("Nenhuma coluna numérica encontrada.")
        return df, None

    default_col = next(
        (c for c in ("BALT", "MACH", "APA", "NZ") if c in numeric_cols),
        numeric_cols[0],
    )
    y_col = st.sidebar.selectbox(
        "Eixo Y",
        options=numeric_cols,
        index=numeric_cols.index(default_col),
    )

    return df, y_col


# -----------------------------------------------------------------------
# Layout Principal
# -----------------------------------------------------------------------

def render_main(df: pd.DataFrame, y_col: str) -> None:
    """Monta o layout de três boxes sincronizados via TimeController."""

    controller    = TimeController(df)
    attitude_box  = AttitudeBox()
    eicas_panel   = EICASPanel()
    subsys_cards  = SubsystemCards()
    fault_columns = _LOADER.get_fault_columns(df)

    # Lê o índice atual do session_state antes de renderizar (para sincronia total)
    time_idx = int(st.session_state.get(TimeController.SESSION_KEY, 0))
    snapshot = controller.get_snapshot(time_idx)

    # Monitor de Dados em tempo real na Sidebar para Debug
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔎 Monitor Real-time")
        q_val = snapshot.get("Q", 0)
        itt_val = snapshot.get("ITT", 0)
        st.write(f"**Tempo:** {snapshot.get('TIME', 0):.2f}s")
        st.write(f"**Torque (Q):** {q_val}")
        st.write(f"**ITT:** {itt_val}")

    # ── Box Superior: Horizonte Artificial + Métricas ───────────────────
    with st.container():
        st.markdown("#### ✈️ Atitude e Dados Críticos")
        attitude_box.render(snapshot)

    st.markdown("---")

    # ── Box Central: Gráfico Temporal ───────────────────────────────────
    with st.container():
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

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"scrollZoom": True, "displayModeBar": True},
        )

    # ── Slider de Tempo (Integrado logo abaixo do gráfico) ─────────────
    time_idx = controller.render_slider()

    # ── Cards de Subsistemas ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🔧 Subsistemas")
    subsys_cards.render_all(snapshot)


# -----------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------

def main() -> None:
    st.title("V.A.D.E.R. 🦅")
    st.caption("Visualizador Analítico de Dados de Engenharia e Rastreio — A-29")

    df, y_col = render_sidebar()

    if df is None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                st.image("assets/a29_sideview.png", use_container_width=True)
            except Exception:
                pass
        st.info("📂 Carregue um arquivo CSV do VADR na barra lateral para iniciar a análise.")
        return

    if y_col is None:
        st.warning("Nenhuma coluna numérica encontrada no arquivo carregado.")
        return

    render_main(df, y_col)


if __name__ == "__main__":
    main()
