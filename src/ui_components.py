"""
ui_components.py
Componentes visuais Streamlit do V.A.D.E.R.

Responsabilidades:
  - Painel EICAS (Engine Indicating and Crew Alerting System)
  - Janela CAS (Crew Alerting System) com tradução de MWC_DATA
  - Cards de Subsistemas: Trem de Pouso, Força G, Motor
  - Controlador de Tempo (Time Scrubbing via st.session_state)
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.plots import EngineGaugePlotter, AttitudeIndicator, TimelinePlotter


# -----------------------------------------------------------------------
# Dicionário de tradução MWC_DATA → texto EICAS
# -----------------------------------------------------------------------

MWC_TRANSLATION: dict[int, tuple[str, str]] = {
    0:  ("", "normal"),           # Operação Normal
    1:  ("ENG MAN - PMU FAIL", "warning"),
    5:  ("OIL PRESS", "caution"),
    27: ("ELEK OVH", "caution"),
    47: ("ENG FIRE", "warning"),
    57: ("ENG LIMIT", "warning"),
}


# -----------------------------------------------------------------------
# Controlador de Tempo Global
# -----------------------------------------------------------------------

class TimeController:
    """Gerencia o estado temporal global via st.session_state."""

    SESSION_KEY: str = "current_time_index"

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        self._init_session_state()

    def _init_session_state(self) -> None:
        """Inicializa st.session_state.current_time_index se ainda não existir."""
        ...

    def render_slider(self, time_column: str = "TIME") -> int:
        """Renderiza o slider de tempo no Streamlit e retorna o índice selecionado.

        Returns:
            Índice inteiro da linha selecionada no DataFrame.
        """
        ...

    def get_snapshot(self, time_index: int) -> pd.Series:
        """Retorna a linha do DataFrame no índice temporal atual."""
        ...


# -----------------------------------------------------------------------
# Painel EICAS Principal
# -----------------------------------------------------------------------

class EICASPanel:
    """Renderiza o painel EICAS completo no layout Streamlit."""

    EICAS_STYLE: str = "background-color: #0E1117; border-radius: 8px; padding: 12px;"

    def __init__(self) -> None:
        self._gauge_plotter = EngineGaugePlotter()

    def render(self, snapshot: pd.Series, fault_columns: list[str]) -> None:
        """Ponto de entrada principal: renderiza todo o painel EICAS para o snapshot.

        Args:
            snapshot: Linha do DataFrame no instante de tempo selecionado.
            fault_columns: Lista de colunas MW* ativas no DataFrame.
        """
        ...

    def render_engine_gauges(self, snapshot: pd.Series) -> None:
        """Renderiza os gauges do motor (Q, ITT, NP, NG, FF, OT, OP) em colunas."""
        ...

    def render_cas_window(self, mwc_code: int, mw_flags: dict[str, int]) -> None:
        """Renderiza a janela CAS com warnings (vermelho) acima de cautions (amarelo).

        Permanece em branco/preta se não houver alertas ativos.
        """
        ...

    def _translate_mwc_code(self, code: int) -> tuple[str, str]:
        """Traduz código numérico MWC_DATA para (texto, severidade).

        Retorna ('', 'normal') para códigos desconhecidos.
        """
        ...

    def _collect_active_faults(self, snapshot: pd.Series, fault_columns: list[str]) -> list[str]:
        """Varre as colunas MW* e retorna os nomes das falhas ativas (== 1)."""
        ...


# -----------------------------------------------------------------------
# Cards de Subsistemas (RF04)
# -----------------------------------------------------------------------

class SubsystemCards:
    """Renderiza os cards informativos do Box Inferior."""

    def render_all(self, snapshot: pd.Series) -> None:
        """Renderiza todos os cards de subsistemas lado a lado em st.columns."""
        ...

    def render_landing_gear_card(self, ldg: int, wow: int) -> None:
        """Exibe card do Trem de Pouso.

        ATENÇÃO À LÓGICA INVERTIDA de LDG: 0 = Abaixado/Travado, 1 = Recolhido.
        WOW: 0 = Solo, 1 = Ar.
        """
        ...

    def render_structural_load_card(self, nz: float) -> None:
        """Exibe card de Carga Estrutural (Força G).

        Dispara alerta visual vermelho se NZ > 4.0G.
        """
        ...

    def render_engine_summary_card(self, snapshot: pd.Series) -> None:
        """Exibe card resumido do motor: ITT, FF e status geral."""
        ...


# -----------------------------------------------------------------------
# Box Superior: Atitude + Altímetro + Velocímetro (RF02)
# -----------------------------------------------------------------------

class AttitudeBox:
    """Renderiza o Box Superior com o horizonte artificial e dados críticos."""

    def __init__(self) -> None:
        self._attitude = AttitudeIndicator()

    def render(self, snapshot: pd.Series) -> None:
        """Renderiza horizonte artificial + altitude (BALT) + velocidade (MACH).

        Args:
            snapshot: Linha do DataFrame no instante selecionado.
        """
        ...
