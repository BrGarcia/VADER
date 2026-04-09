"""
plots.py
Funções geradoras de todos os gráficos Plotly do V.A.D.E.R.

Módulos cobertos:
  - Gráfico de linha do tempo (RF03)
  - Horizonte Artificial / Atitude (RF02)
  - Gauges do Motor via go.Indicator (Fase 2 / Guia EICAS §2)
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


# -----------------------------------------------------------------------
# Constantes de Limites Operacionais
# -----------------------------------------------------------------------

ENGINE_LIMITS: dict[str, dict] = {
    "ITT":  {"caution": 850, "warning": 1000},   # °C
    "Q":    {"caution": 100, "warning": 120},     # %
    "NP":   {"caution": 100, "warning": 110},     # %
    "NG":   {"caution": 100, "warning": 110},     # %
    "FF":   {"caution": 420, "warning": 480},     # kg/h
    "OT":   {"caution": 120, "warning": 140},     # °C
    "OP":   {"caution": 20,  "warning": 10},      # PSI (limite mínimo)
}

COLORS = {
    "normal":  "#FFFFFF",
    "caution": "#FFC107",
    "warning": "#FF4B4B",
    "background": "#0E1117",
}

NZ_ALERT_THRESHOLD: float = 4.0  # G


# -----------------------------------------------------------------------
# Módulo de Análise Temporal (RF03)
# -----------------------------------------------------------------------

class TimelinePlotter:
    """Gera o gráfico 2D principal (Eixo X = TIME, Eixo Y = variável selecionada)."""

    def plot(self, df: pd.DataFrame, y_column: str, time_column: str = "TIME") -> go.Figure:
        """Plota série temporal interativa com zoom/pan habilitados.

        Args:
            df: DataFrame processado.
            y_column: Nome da coluna a exibir no Eixo Y.
            time_column: Coluna de tempo a usar como Eixo X.

        Returns:
            Figura Plotly pronta para `st.plotly_chart`.
        """
        ...

    def add_fault_markers(self, fig: go.Figure, df: pd.DataFrame, fault_columns: list[str]) -> go.Figure:
        """Sobrepõe marcadores verticais no gráfico nos instantes de falha (MW* == 1).

        Args:
            fig: Figura já gerada por `plot()`.
            df: DataFrame com colunas MW*.
            fault_columns: Lista de colunas de falha a varrer.

        Returns:
            Figura atualizada com os marcadores de falha.
        """
        ...

    def add_phase_bands(self, fig: go.Figure, df: pd.DataFrame) -> go.Figure:
        """Destaca visualmente as fases de voo (solo / decolagem / cruzeiro / pouso)
        usando a variável WOW como base."""
        ...


# -----------------------------------------------------------------------
# Módulo de Posição e Atitude (RF02)
# -----------------------------------------------------------------------

class AttitudeIndicator:
    """Gera a representação do Horizonte Artificial (pitch + roll)."""

    def plot(self, pitch: float, roll: float) -> go.Figure:
        """Renderiza o horizonte artificial para os valores instantâneos de pitch/roll.

        Args:
            pitch: Valor de APA (graus).
            roll: Valor de ARA (graus).

        Returns:
            Figura Plotly com a representação do horizonte.
        """
        ...


# -----------------------------------------------------------------------
# Módulo do Grupo Motopropulsor - Gauges (Fase 2 / EICAS §2)
# -----------------------------------------------------------------------

class EngineGaugePlotter:
    """Gera os gauges/bullets dos instrumentos do motor via go.Indicator."""

    def plot_gauge(self, value: float, variable: str, label: str) -> go.Figure:
        """Cria um gauge Plotly para a variável de motor fornecida.

        A cor da barra muda dinamicamente conforme os thresholds em ENGINE_LIMITS.

        Args:
            value: Valor instantâneo lido do DataFrame.
            variable: Chave em ENGINE_LIMITS (ex: 'ITT', 'Q').
            label: Texto de exibição no gauge.

        Returns:
            Figura Plotly com o gauge configurado.
        """
        ...

    def _get_color(self, value: float, variable: str) -> str:
        """Retorna a cor correta (normal / caution / warning) para o valor."""
        ...

    def plot_all_engine_gauges(self, snapshot: pd.Series) -> list[go.Figure]:
        """Gera a lista completa de gauges para o snapshot temporal atual.

        Returns:
            Lista de figuras: [Q, ITT, NP, NG, FF, OT, OP]
        """
        ...
