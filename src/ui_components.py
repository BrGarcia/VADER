"""
ui_components.py
Componentes visuais Streamlit do V.A.D.E.R.

Fase 1 (implementado):
  - TimeController  — slider de tempo + session_state
  - AttitudeBox     — horizonte artificial + métricas críticas

Fase 2/3 (skeleton):
  - EICASPanel, SubsystemCards
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.plots import EngineGaugePlotter, AttitudeIndicator, TimelinePlotter


# -----------------------------------------------------------------------
# Dicionário de tradução MWC_DATA → texto EICAS  (Fase 3)
# -----------------------------------------------------------------------

MWC_TRANSLATION: dict[int, tuple[str, str]] = {
    0:  ("", "normal"),
    1:  ("ENG MAN - PMU FAIL", "warning"),
    5:  ("OIL PRESS", "caution"),
    27: ("ELEK OVH", "caution"),
    47: ("ENG FIRE", "warning"),
    57: ("ENG LIMIT", "warning"),
}


# -----------------------------------------------------------------------
# Controlador de Tempo Global — Fase 1
# -----------------------------------------------------------------------

class TimeController:
    """Gerencia o estado temporal global via st.session_state."""

    SESSION_KEY: str = "current_time_index"

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        self._init_session_state()

    def _init_session_state(self) -> None:
        """Inicializa st.session_state.current_time_index na primeira execução."""
        if self.SESSION_KEY not in st.session_state:
            st.session_state[self.SESSION_KEY] = 0

    def render_slider(self, time_column: str = "TIME") -> int:
        """Renderiza o slider de tempo e retorna o índice selecionado."""
        n = len(self.df)
        if n == 0:
            return 0

        # Calcula label do instante atual para exibição no slider
        current_idx: int = st.session_state.get(self.SESSION_KEY, 0)
        current_idx = max(0, min(current_idx, n - 1))

        time_str = ""
        if "TIME_STR" in self.df.columns:
            time_str = str(self.df.iloc[current_idx].get("TIME_STR", ""))
        elif time_column in self.df.columns:
            time_str = f"{self.df.iloc[current_idx][time_column]:.3f}s"

        col_slider, col_label = st.columns([5, 1])
        with col_slider:
            idx: int = st.slider(
                "⏱ Linha do Tempo",
                min_value=0,
                max_value=n - 1,
                value=current_idx,
                key=self.SESSION_KEY,
                help="Arraste para navegar pela gravação de voo",
            )
        with col_label:
            st.markdown(
                f"<div style='padding-top:28px; font-family:monospace; color:#00FF88;'>"
                f"  {time_str}"
                f"</div>",
                unsafe_allow_html=True,
            )

        return int(idx)

    def get_snapshot(self, time_index: int) -> pd.Series:
        """Retorna a linha do DataFrame no índice temporal atual."""
        idx = max(0, min(time_index, len(self.df) - 1))
        return self.df.iloc[idx]


# -----------------------------------------------------------------------
# Box Superior: Horizonte Artificial + Dados Críticos — Fase 1
# -----------------------------------------------------------------------

class AttitudeBox:
    """Renderiza o Box Superior com o horizonte artificial e dados críticos."""

    def __init__(self) -> None:
        self._attitude = AttitudeIndicator()

    def render(self, snapshot: pd.Series) -> None:
        """Renderiza horizonte artificial + altitude (BALT) + velocidade (MACH)."""

        def _safe(key: float | str, fallback: float = 0.0) -> float:
            val = snapshot.get(key, fallback)
            try:
                f = float(val)
                return f if f == f else fallback  # NaN check
            except Exception:
                return fallback

        pitch    = _safe("APA")
        roll     = _safe("ARA")
        altitude = _safe("BALT", _safe("PALT"))
        speed    = _safe("MACH", _safe("AS"))
        nz       = _safe("NZ")
        aoa      = _safe("AOA")

        col_horizon, col_metrics = st.columns([3, 1])

        with col_horizon:
            fig = self._attitude.plot(pitch, roll)
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={"displayModeBar": False, "staticPlot": False},
            )

        with col_metrics:
            nz_color = "#FF4B4B" if abs(nz) > 4.0 else "#00FF88"
            st.markdown(
                f"""
                <div style="
                    font-family: monospace;
                    background: #0E1117;
                    border: 1px solid #2D2D2D;
                    border-radius: 8px;
                    padding: 14px 10px;
                    text-align: center;
                    line-height: 1.3;
                ">
                    <div style="font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">ALT (ft)</div>
                    <div style="font-size:1.8rem; font-weight:bold; color:#00FF88;">{altitude:,.0f}</div>

                    <div style="margin-top:8px; font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">MACH</div>
                    <div style="font-size:1.8rem; font-weight:bold; color:#00FF88;">{speed:.3f}</div>

                    <div style="margin-top:8px; font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">PITCH</div>
                    <div style="font-size:1.1rem; color:#FFC107;">{pitch:+.1f}°</div>

                    <div style="margin-top:4px; font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">ROLL</div>
                    <div style="font-size:1.1rem; color:#FFC107;">{roll:+.1f}°</div>

                    <div style="margin-top:8px; font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">NZ (G)</div>
                    <div style="font-size:1.4rem; font-weight:bold; color:{nz_color};">{nz:+.2f}G</div>

                    <div style="margin-top:4px; font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:1px;">AOA</div>
                    <div style="font-size:1.0rem; color:#FAFAFA;">{aoa:.1f}°</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# -----------------------------------------------------------------------
# Painel EICAS Principal — Fase 2/3 (skeleton)
# -----------------------------------------------------------------------

class EICASPanel:
    """Renderiza o painel EICAS completo. (Fase 2/3)"""

    EICAS_STYLE: str = "background-color: #0E1117; border-radius: 8px; padding: 12px;"

    def __init__(self) -> None:
        self._gauge_plotter = EngineGaugePlotter()

    def render(self, snapshot: pd.Series, fault_columns: list[str]) -> None:
        """Ponto de entrada principal: renderiza todo o painel EICAS. (Fase 2/3)"""
        ...

    def render_engine_gauges(self, snapshot: pd.Series) -> None:
        """Renderiza os gauges do motor em colunas. (Fase 2)"""
        ...

    def render_cas_window(self, mwc_code: int, mw_flags: dict[str, int]) -> None:
        """Renderiza a janela CAS com warnings acima de cautions. (Fase 3)"""
        ...

    def _translate_mwc_code(self, code: int) -> tuple[str, str]:
        """Traduz código MWC_DATA para (texto, severidade). (Fase 3)"""
        ...

    def _collect_active_faults(self, snapshot: pd.Series, fault_columns: list[str]) -> list[str]:
        """Varre as colunas MW* e retorna os nomes das falhas ativas == 1. (Fase 3)"""
        ...


# -----------------------------------------------------------------------
# Cards de Subsistemas — Fase 2 (skeleton)
# -----------------------------------------------------------------------

class SubsystemCards:
    """Renderiza os cards informativos do Box Inferior. (Fase 2)"""

    def render_all(self, snapshot: pd.Series) -> None: ...

    def render_landing_gear_card(self, ldg: int, wow: int) -> None: ...

    def render_structural_load_card(self, nz: float) -> None: ...

    def render_engine_summary_card(self, snapshot: pd.Series) -> None: ...
