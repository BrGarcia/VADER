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
# Painel EICAS Principal — Fase 2 (gauges) / Fase 3 (CAS — skeleton)
# -----------------------------------------------------------------------

class EICASPanel:
    """Renderiza o painel EICAS completo no layout Streamlit."""

    EICAS_STYLE: str = "background-color: #0E1117; border-radius: 8px; padding: 12px;"

    def __init__(self) -> None:
        self._gauge_plotter = EngineGaugePlotter()

    def render(self, snapshot: pd.Series, fault_columns: list[str]) -> None:
        """Ponto de entrada principal do painel EICAS para o snapshot atual."""
        self.render_engine_gauges(snapshot)
        # Fase 3: self.render_cas_window(...)

    def render_engine_gauges(self, snapshot: pd.Series) -> None:
        """Renderiza os 7 gauges do motor (Q, ITT, NP, NG, FF, OT, OP) em colunas."""
        st.markdown(
            "<div style='background:#0E1117; border:1px solid #2D2D2D; "
            "border-radius:8px; padding:6px 4px 0px 4px;'>",
            unsafe_allow_html=True,
        )

        figs = self._gauge_plotter.plot_all_engine_gauges(snapshot)
        cols = st.columns(7)
        for col, fig in zip(cols, figs):
            with col:
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={"displayModeBar": False, "staticPlot": True},
                )

        st.markdown("</div>", unsafe_allow_html=True)

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
# Cards de Subsistemas — Fase 2
# -----------------------------------------------------------------------

class SubsystemCards:
    """Renderiza os cards informativos do Box Inferior."""

    _CARD_BASE = (
        "background:#0E1117; border:1px solid #2D2D2D; border-radius:8px; "
        "padding:12px; text-align:center; font-family:monospace;"
    )

    def render_all(self, snapshot: pd.Series) -> None:
        """Renderiza os quatro cards de subsistemas lado a lado."""

        def _safe(key: str, fallback: float = 0.0) -> float:
            val = snapshot.get(key, fallback)
            try:
                f = float(val)
                return f if f == f else fallback
            except Exception:
                return fallback

        ldg = int(_safe("LDG"))
        wow = int(_safe("WOW"))
        nz  = _safe("NZ")

        col_gear, col_nz, col_engine, col_pcl = st.columns(4)

        with col_gear:
            self.render_landing_gear_card(ldg, wow)
        with col_nz:
            self.render_structural_load_card(nz)
        with col_engine:
            self.render_engine_summary_card(snapshot)
        with col_pcl:
            self._render_pcl_card(_safe("PCL"))

    def render_landing_gear_card(self, ldg: int, wow: int) -> None:
        """Exibe o card do Trem de Pouso.

        Lógica LDG (invertida conforme dicionário de dados):
            LDG == 0  →  Abaixado / Travado  (verde)
            LDG == 1  →  Recolhido           (amarelo)
        Lógica WOW:
            WOW == 1  →  Solo
            WOW == 0  →  Ar
        """
        gear_label = "ABAIXADO ✓" if ldg == 0 else "RECOLHIDO"
        gear_color = "#00FF88" if ldg == 0 else "#FFC107"
        phase_label = "SOLO" if wow == 1 else "AR"
        phase_color = "#A07850" if wow == 1 else "#4A90D9"

        st.markdown(
            f"<div style='{self._CARD_BASE}'>"
            f"  <div style='font-size:0.65rem;color:#888;letter-spacing:1px;'>TREM DE POUSO</div>"
            f"  <div style='font-size:1.1rem;font-weight:bold;color:{gear_color};'>{gear_label}</div>"
            f"  <div style='font-size:0.75rem;font-weight:bold;color:{phase_color};margin-top:4px;'>{phase_label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    def render_structural_load_card(self, nz: float) -> None:
        """Exibe card de Carga Estrutural (Força G). Alerta visual se NZ > 4.0G."""
        alert = abs(nz) > NZ_ALERT_THRESHOLD
        nz_color = "#FF4B4B" if alert else "#00FF88"
        border_color = "#FF4B4B" if alert else "#2D2D2D"
        alert_text = "<div style='font-size:0.65rem;color:#FF4B4B;'>⚠ LIMITE ESTRUTURAL</div>" if alert else ""

        st.markdown(
            f"<div style='{self._CARD_BASE} border-color:{border_color};'>"
            f"  <div style='font-size:0.65rem;color:#888;letter-spacing:1px;'>CARGA ESTRUTURAL</div>"
            f"  <div style='font-size:1.6rem;font-weight:bold;color:{nz_color};'>{nz:+.2f} G</div>"
            f"  {alert_text}"
            f"</div>",
            unsafe_allow_html=True,
        )

    def render_engine_summary_card(self, snapshot: pd.Series) -> None:
        """Exibe card resumido do motor: ITT, FF e status geral."""
        def _safe(k: str) -> float:
            v = snapshot.get(k, 0)
            try:
                f = float(v)
                return f if f == f else 0.0
            except Exception:
                return 0.0

        itt = _safe("ITT")
        ff  = _safe("FF")
        ng  = _safe("NG")

        itt_color = "#FF4B4B" if itt > 1000 else "#FFC107" if itt > 850 else "#00FF88"
        ff_color  = "#FF4B4B" if ff  > 480  else "#FFC107" if ff  > 420 else "#00FF88"

        st.markdown(
            f"<div style='{self._CARD_BASE}'>"
            f"  <div style='font-size:0.65rem;color:#888;letter-spacing:1px;'>MOTOR</div>"
            f"  <div style='font-size:0.8rem;margin-top:4px;'>"
            f"    <span style='color:#888;'>ITT </span>"
            f"    <span style='color:{itt_color};font-weight:bold;'>{itt:.0f}°C</span>"
            f"  </div>"
            f"  <div style='font-size:0.8rem;margin-top:2px;'>"
            f"    <span style='color:#888;'>FF &nbsp;</span>"
            f"    <span style='color:{ff_color};font-weight:bold;'>{ff:.0f} kg/h</span>"
            f"  </div>"
            f"  <div style='font-size:0.8rem;margin-top:2px;'>"
            f"    <span style='color:#888;'>Ng &nbsp;</span>"
            f"    <span style='color:#FAFAFA;'>{ng:.1f}%</span>"
            f"  </div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    def _render_pcl_card(self, pcl: float) -> None:
        """Exibe a posição da Manete de Potência (PCL)."""
        # PCL range operacional: -20 a +179°
        # Zonas aproximadas: < 0° = Ground Idle, 0-60° = Flight Idle→Cruise, > 130° = Max Power
        if pcl < 0:
            pcl_label, pcl_color = "GROUND IDLE", "#4A90D9"
        elif pcl < 60:
            pcl_label, pcl_color = "IDLE / CRUISE", "#00FF88"
        elif pcl < 130:
            pcl_label, pcl_color = "CRUISE / CLIMB", "#FFC107"
        else:
            pcl_label, pcl_color = "MAX POWER", "#FF4B4B"

        st.markdown(
            f"<div style='{self._CARD_BASE}'>"
            f"  <div style='font-size:0.65rem;color:#888;letter-spacing:1px;'>MANETE (PCL)</div>"
            f"  <div style='font-size:1.6rem;font-weight:bold;color:{pcl_color};'>{pcl:.1f}°</div>"
            f"  <div style='font-size:0.7rem;color:{pcl_color};margin-top:2px;'>{pcl_label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
