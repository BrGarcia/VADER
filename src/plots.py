"""
plots.py
Funções geradoras de todos os gráficos Plotly do V.A.D.E.R.

Módulos cobertos:
  - Gráfico de linha do tempo (RF03)          ← Fase 1
  - Horizonte Artificial / Atitude (RF02)     ← Fase 1
  - Gauges do Motor via go.Indicator (EICAS)  ← Fase 2 (skeleton mantido)
"""

from __future__ import annotations

import math
import pandas as pd
import plotly.graph_objects as go


# -----------------------------------------------------------------------
# Constantes de Limites Operacionais (Fase 2)
# -----------------------------------------------------------------------

ENGINE_LIMITS: dict[str, dict] = {
    "ITT": {"caution": 850,  "warning": 1000},   # °C
    "Q":   {"caution": 100,  "warning": 120},     # %
    "NP":  {"caution": 100,  "warning": 110},     # %
    "NG":  {"caution": 100,  "warning": 110},     # %
    "FF":  {"caution": 420,  "warning": 480},     # kg/h
    "OT":  {"caution": 120,  "warning": 140},     # °C
    "OP":  {"caution": 20,   "warning": 10},      # PSI (limite mínimo)
}

COLORS = {
    "normal":     "#FFFFFF",
    "caution":    "#FFC107",
    "warning":    "#FF4B4B",
    "background": "#0E1117",
    "sky":        "#4A90D9",
    "ground":     "#6B4226",
    "horizon":    "#FFFFFF",
    "accent":     "#FFD700",
    "cursor":     "#FF4B4B",
    "trace":      "#00B4D8",
    "grid":       "#2D2D2D",
}

NZ_ALERT_THRESHOLD: float = 4.0  # G


# -----------------------------------------------------------------------
# Módulo de Análise Temporal — RF03
# -----------------------------------------------------------------------

class TimelinePlotter:
    """Gera o gráfico 2D principal (Eixo X = TIME, Eixo Y = variável selecionada)."""

    def plot(self, df: pd.DataFrame, y_column: str, time_column: str = "TIME") -> go.Figure:
        """Plota série temporal interativa com zoom/pan habilitados."""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df[time_column],
            y=df[y_column],
            mode="lines",
            name=y_column,
            line=dict(color=COLORS["trace"], width=1.5),
            hovertemplate=(
                f"<b>Tempo:</b> %{{x:.3f}} s<br>"
                f"<b>{y_column}:</b> %{{y}}<extra></extra>"
            ),
        ))

        fig.update_layout(
            plot_bgcolor=COLORS["background"],
            paper_bgcolor=COLORS["background"],
            font=dict(color="#FAFAFA", family="monospace", size=12),
            xaxis=dict(
                title="Tempo (s)",
                showgrid=True,
                gridcolor=COLORS["grid"],
                color="#FAFAFA",
                zeroline=False,
            ),
            yaxis=dict(
                title=y_column,
                showgrid=True,
                gridcolor=COLORS["grid"],
                color="#FAFAFA",
                zeroline=False,
            ),
            margin=dict(l=60, r=20, t=20, b=50),
            height=320,
            dragmode="zoom",
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )

        return fig

    def add_fault_markers(
        self, fig: go.Figure, df: pd.DataFrame, fault_columns: list[str]
    ) -> go.Figure:
        """Sobrepõe marcadores no gráfico nos instantes em que uma falha MW* == 1."""
        if "TIME" not in df.columns or not fault_columns:
            return fig

        for col in fault_columns:
            if col not in df.columns:
                continue
            fault_times = df.loc[df[col] == 1, "TIME"]
            if fault_times.empty:
                continue

            fig.add_trace(go.Scatter(
                x=fault_times,
                y=[df[df["TIME"] == t].iloc[0].get("BALT", 0) for t in fault_times],
                mode="markers",
                name=col,
                marker=dict(
                    symbol="x",
                    color=COLORS["warning"],
                    size=8,
                    line=dict(width=2),
                ),
                hovertemplate=f"<b>FALHA: {col}</b><br>t=%{{x:.3f}}s<extra></extra>",
            ))

        return fig

    def add_phase_bands(self, fig: go.Figure, df: pd.DataFrame) -> go.Figure:
        """Destaca fases de solo (WOW == 0) com banda marrom translúcida."""
        if "WOW" not in df.columns or "TIME" not in df.columns:
            return fig

        wow_data = df[["TIME", "WOW"]].dropna(subset=["WOW"])
        if wow_data.empty:
            return fig

        in_ground = False
        band_start: float | None = None

        for _, row in wow_data.iterrows():
            on_ground = int(row["WOW"]) == 0
            t = float(row["TIME"])

            if on_ground and not in_ground:
                in_ground = True
                band_start = t
            elif not on_ground and in_ground:
                in_ground = False
                if band_start is not None:
                    fig.add_vrect(
                        x0=band_start, x1=t,
                        fillcolor="rgba(107, 66, 38, 0.20)",
                        line_width=0,
                        annotation_text="Solo",
                        annotation_font=dict(color="#A07850", size=10),
                        annotation_position="top left",
                    )

        if in_ground and band_start is not None:
            fig.add_vrect(
                x0=band_start, x1=float(wow_data["TIME"].max()),
                fillcolor="rgba(107, 66, 38, 0.20)",
                line_width=0,
            )

        return fig


# -----------------------------------------------------------------------
# Módulo de Posição e Atitude — RF02
# -----------------------------------------------------------------------

class AttitudeIndicator:
    """Gera a representação do Horizonte Artificial (pitch + roll)."""

    _PITCH_SCALE: float = 1 / 30    # 1 display unit por 30° de pitch
    _ROLL_ARC_R: float = 0.82       # raio do arco de roll
    _VIEWPORT: float = 1.0

    def plot(self, pitch: float, roll: float) -> go.Figure:
        """Renderiza o horizonte artificial para os valores instantâneos de pitch/roll."""
        # Tratar NaN
        pitch = 0.0 if pitch != pitch else float(pitch)
        roll  = 0.0 if roll  != roll  else float(roll)

        fig = go.Figure()

        # --- Solo (polígono abaixo do horizonte) ---
        gx, gy = self._ground_polygon(pitch, roll)
        if gx:
            fig.add_trace(go.Scatter(
                x=gx, y=gy,
                fill="toself",
                fillcolor=COLORS["ground"],
                line=dict(color=COLORS["ground"], width=0),
                mode="lines",
                showlegend=False,
                hoverinfo="skip",
            ))

        # --- Linha do horizonte ---
        roll_rad = math.radians(-roll)
        W = 1.5
        hx = [-W * math.cos(roll_rad), W * math.cos(roll_rad)]
        hy_base = -pitch * self._PITCH_SCALE
        hy = [
            hy_base - W * math.sin(roll_rad),
            hy_base + W * math.sin(roll_rad),
        ]
        fig.add_trace(go.Scatter(
            x=hx, y=hy,
            mode="lines",
            line=dict(color=COLORS["horizon"], width=2),
            showlegend=False,
            hoverinfo="skip",
        ))

        # --- Escada de Pitch (linhas de referência) ---
        for angle in [-20, -15, -10, -5, 5, 10, 15, 20]:
            y_pos = -(pitch - angle) * self._PITCH_SCALE
            if abs(y_pos) > 0.88:
                continue
            hw = 0.18 if angle % 10 == 0 else 0.10
            fig.add_trace(go.Scatter(
                x=[-hw, hw], y=[y_pos, y_pos],
                mode="lines",
                line=dict(color="rgba(255,255,255,0.6)", width=1),
                showlegend=False,
                hoverinfo="skip",
            ))
            # Rótulo no lado direito
            fig.add_annotation(
                x=hw + 0.04, y=y_pos,
                text=str(abs(angle)),
                showarrow=False,
                font=dict(color="rgba(255,255,255,0.5)", size=8, family="monospace"),
                xanchor="left",
            )

        # --- Símbolo de aeronave (fixo no centro) ---
        for xs, ys in [
            ([-0.45, -0.20, -0.20], [0.0, 0.0, -0.06]),   # asa esquerda
            ([0.45,  0.20,  0.20],  [0.0, 0.0, -0.06]),   # asa direita
            ([-0.06, 0.06], [0.0, 0.0]),                   # fuselagem
        ]:
            fig.add_trace(go.Scatter(
                x=xs, y=ys,
                mode="lines",
                line=dict(color=COLORS["accent"], width=3),
                showlegend=False,
                hoverinfo="skip",
            ))
        fig.add_trace(go.Scatter(
            x=[0], y=[0],
            mode="markers",
            marker=dict(color=COLORS["accent"], size=5),
            showlegend=False,
            hoverinfo="skip",
        ))

        # --- Arco de Roll ---
        arc_theta = range(-65, 66)
        arc_x = [self._ROLL_ARC_R * math.sin(math.radians(a)) for a in arc_theta]
        arc_y = [self._ROLL_ARC_R * math.cos(math.radians(a)) for a in arc_theta]
        fig.add_trace(go.Scatter(
            x=arc_x, y=arc_y,
            mode="lines",
            line=dict(color="rgba(255,255,255,0.5)", width=1),
            showlegend=False,
            hoverinfo="skip",
        ))

        # Marcações no arco (±10, ±20, ±30, ±45, ±60)
        for tick_deg in [-60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60]:
            t_rad = math.radians(tick_deg)
            t_len = 0.06 if tick_deg % 30 == 0 else 0.03
            r_in = self._ROLL_ARC_R
            fig.add_trace(go.Scatter(
                x=[r_in * math.sin(t_rad), (r_in + t_len) * math.sin(t_rad)],
                y=[r_in * math.cos(t_rad), (r_in + t_len) * math.cos(t_rad)],
                mode="lines",
                line=dict(color="rgba(255,255,255,0.7)", width=1),
                showlegend=False,
                hoverinfo="skip",
            ))

        # Ponteiro de Roll (triângulo indicando bank atual)
        roll_rad_ptr = math.radians(roll)
        r = self._ROLL_ARC_R
        tip_x = r * math.sin(roll_rad_ptr)
        tip_y = r * math.cos(roll_rad_ptr)
        base_r = r + 0.07
        half = math.radians(4)
        fig.add_trace(go.Scatter(
            x=[
                base_r * math.sin(roll_rad_ptr - half),
                tip_x,
                base_r * math.sin(roll_rad_ptr + half),
                base_r * math.sin(roll_rad_ptr - half),
            ],
            y=[
                base_r * math.cos(roll_rad_ptr - half),
                tip_y,
                base_r * math.cos(roll_rad_ptr + half),
                base_r * math.cos(roll_rad_ptr - half),
            ],
            fill="toself",
            fillcolor="white",
            line=dict(color="white", width=1),
            mode="lines",
            showlegend=False,
            hoverinfo="skip",
        ))

        fig.update_layout(
            paper_bgcolor=COLORS["sky"],
            plot_bgcolor=COLORS["sky"],
            xaxis=dict(range=[-1, 1], visible=False, scaleanchor="y", scaleratio=1),
            yaxis=dict(range=[-1, 1], visible=False),
            margin=dict(l=0, r=0, t=0, b=0),
            height=220,
            showlegend=False,
        )

        return fig

    def _ground_polygon(self, pitch: float, roll: float) -> tuple[list, list]:
        """Calcula os vértices do polígono do solo (abaixo da linha do horizonte)."""
        y_h = -pitch * self._PITCH_SCALE
        y_h = max(-1.5, min(1.5, y_h))

        try:
            slope = math.tan(math.radians(-roll))
        except Exception:
            slope = 0.0

        # "Solo" = pontos onde y <= y_h + slope * x
        def is_ground(x: float, y: float) -> bool:
            return y <= y_h + slope * x

        corners = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]
        edges = [
            (corners[0], corners[1]),
            (corners[1], corners[2]),
            (corners[2], corners[3]),
            (corners[3], corners[0]),
        ]

        intersections: list[tuple[float, float]] = []
        for (x1, y1), (x2, y2) in edges:
            dx, dy = x2 - x1, y2 - y1
            denom = dy - slope * dx
            if abs(denom) < 1e-9:
                continue
            t = (y_h + slope * x1 - y1) / denom
            if 0.0 <= t <= 1.0:
                intersections.append((x1 + t * dx, y1 + t * dy))

        ground_corners = [(cx, cy) for cx, cy in corners if is_ground(cx, cy)]
        pts = intersections + ground_corners

        if len(pts) < 3:
            # Todo o viewport é solo
            if is_ground(0.0, 0.0):
                return [-1, 1, 1, -1, -1], [-1, -1, 1, 1, -1]
            return [], []

        # Ordenar CCW pelo ângulo a partir do centróide
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        pts.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))

        xs = [p[0] for p in pts] + [pts[0][0]]
        ys = [p[1] for p in pts] + [pts[0][1]]
        return xs, ys


# -----------------------------------------------------------------------
# Módulo do Grupo Motopropulsor — Gauges (Fase 2 — skeleton)
# -----------------------------------------------------------------------

class EngineGaugePlotter:
    """Gera os gauges/bullets dos instrumentos do motor via go.Indicator."""

    def plot_gauge(self, value: float, variable: str, label: str) -> go.Figure:
        """Cria um gauge Plotly para a variável de motor fornecida. (Fase 2)"""
        ...

    def _get_color(self, value: float, variable: str) -> str:
        """Retorna a cor correta (normal / caution / warning) para o valor. (Fase 2)"""
        ...

    def plot_all_engine_gauges(self, snapshot: pd.Series) -> list[go.Figure]:
        """Gera a lista completa de gauges para o snapshot temporal atual. (Fase 2)"""
        ...
