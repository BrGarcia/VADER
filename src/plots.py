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

        t_min = float(df[time_column].min())
        t_max = float(df[time_column].max())

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
                range=[t_min, t_max],
                minallowed=t_min,
                maxallowed=t_max,
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
        self,
        fig: go.Figure,
        df: pd.DataFrame,
        fault_columns: list[str],
        y_column: str = "BALT",
    ) -> go.Figure:
        """Sobrepõe marcadores no gráfico nos instantes em que uma falha MW* == 1.

        Os marcadores são plotados no valor real da série temporal selecionada
        (y_column) para que fiquem visíveis sobre a curva.

        Args:
            fig: Figura gerada por `plot()`.
            df: DataFrame com colunas MW*.
            fault_columns: Colunas a varrer (prefixo MW1_/MW2_/MW3_).
            y_column: Coluna cujos valores são usados como coordenada Y dos marcadores.
        """
        if "TIME" not in df.columns or not fault_columns:
            return fig

        y_col = y_column if y_column in df.columns else None

        for col in fault_columns:
            if col not in df.columns:
                continue

            fault_mask = df[col] == 1
            if not fault_mask.any():
                continue

            fault_rows = df.loc[fault_mask]
            x_vals = fault_rows["TIME"]
            y_vals = fault_rows[y_col] if y_col else pd.Series(
                [0.0] * len(fault_rows), index=fault_rows.index
            )

            # Rótulo limpo: remove prefixo MW*_
            short_name = col.split("_", 1)[-1] if "_" in col else col

            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="markers",
                name=col,
                legendgroup="faults",
                legendgrouptitle=dict(text="Falhas") if col == fault_columns[0] else None,
                marker=dict(
                    symbol="x-open",
                    color=COLORS["warning"],
                    size=10,
                    line=dict(width=2),
                ),
                hovertemplate=(
                    f"<b>⚠ FALHA: {short_name}</b><br>"
                    f"t=%{{x:.3f}} s<br>"
                    f"{y_column}=%{{y}}<extra></extra>"
                ),
            ))

        return fig

    def add_phase_bands(self, fig: go.Figure, df: pd.DataFrame) -> go.Figure:
        """Destaca fases de voo (azul) e solo (marrom) com base no sinal WOW.

        Lógica do sensor WOW (Weight on Wheels):
            WOW == 1  →  peso nas rodas  →  SOLO   (marrom)
            WOW == 0  →  sem peso        →  VOO    (azul)
        """
        if "WOW" not in df.columns or "TIME" not in df.columns:
            return fig

        wow_data = df[["TIME", "WOW"]].dropna(subset=["WOW"])
        if wow_data.empty:
            return fig

        _PHASE_STYLE = {
            "ground": dict(
                fillcolor="rgba(107, 66, 38, 0.22)",
                label="Solo",
                label_color="#A07850",
            ),
            "flight": dict(
                fillcolor="rgba(74, 144, 217, 0.15)",
                label="Voo",
                label_color="#4A90D9",
            ),
        }

        t_max = float(wow_data["TIME"].max())

        # Vectorized run detection — avoids iterrows over every sample row
        phases = (wow_data["WOW"].astype(float).fillna(0).astype(int) == 1).map(
            {True: "ground", False: "flight"}
        )
        run_id = phases.ne(phases.shift()).cumsum()

        first_annotated: set[str] = set()

        for _, group in wow_data.groupby(run_id, sort=False):
            phase = phases.iloc[group.index[0]]
            t_start = float(group["TIME"].iloc[0])
            next_pos = group.index[-1] + 1
            t_end = float(wow_data["TIME"].iloc[next_pos]) if next_pos < len(wow_data) else t_max

            style = _PHASE_STYLE[phase]
            annotate = phase not in first_annotated
            kwargs: dict = dict(x0=t_start, x1=t_end, fillcolor=style["fillcolor"], line_width=0)
            if annotate:
                kwargs.update(
                    annotation_text=style["label"],
                    annotation_font=dict(color=style["label_color"], size=10),
                    annotation_position="top left",
                )
                first_annotated.add(phase)
            fig.add_vrect(**kwargs)

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
# Módulo do Grupo Motopropulsor — Gauges (Fase 2)
# -----------------------------------------------------------------------

# Especificação de faixa e unidade de cada instrumento do motor
GAUGE_SPECS: dict[str, dict] = {
    "Q":   {"min": 0,   "max": 130,  "unit": "%",    "label": "TORQUE"},
    "ITT": {"min": 0,   "max": 1100, "unit": "°C",   "label": "ITT"},
    "NP":  {"min": 0,   "max": 120,  "unit": "%",    "label": "Np"},
    "NG":  {"min": 0,   "max": 115,  "unit": "%",    "label": "Ng"},
    "FF":  {"min": 0,   "max": 500,  "unit": "kg/h", "label": "F.FLOW"},
    "OT":  {"min": 0,   "max": 150,  "unit": "°C",   "label": "OIL TEMP"},
    "OP":  {"min": 0,   "max": 200,  "unit": "PSI",  "label": "OIL PRESS"},
}

# Variáveis cujo limite é mínimo (abaixo = problema), ao contrário das demais
_MIN_LIMIT_VARS: frozenset[str] = frozenset({"OP"})


class EngineGaugePlotter:
    """Gera os gauges dos instrumentos do motor via go.Indicator."""

    def _get_color(self, value: float, variable: str) -> str:
        """Retorna a cor (normal / caution / warning) para o valor instantâneo."""
        limits = ENGINE_LIMITS.get(variable)
        if limits is None:
            return COLORS["normal"]

        caution = limits["caution"]
        warning = limits["warning"]

        if variable in _MIN_LIMIT_VARS:
            # OP: abaixo do limite é ruim
            if value <= warning:
                return COLORS["warning"]
            if value <= caution:
                return COLORS["caution"]
        else:
            if value >= warning:
                return COLORS["warning"]
            if value >= caution:
                return COLORS["caution"]

        return COLORS["normal"]

    def plot_gauge(self, value: float, variable: str, label: str) -> go.Figure:
        """Cria um gauge Plotly para a variável de motor fornecida.

        A cor do needle e do número muda dinamicamente conforme ENGINE_LIMITS.
        """
        spec = GAUGE_SPECS.get(variable, {"min": 0, "max": 100, "unit": "", "label": label})
        limits = ENGINE_LIMITS.get(variable, {})

        v_min = spec["min"]
        v_max = spec["max"]
        safe_value = value if (value == value and value is not None) else 0.0
        bar_color = self._get_color(safe_value, variable)

        caution_val = limits.get("caution", v_max * 0.80)
        warning_val = limits.get("warning", v_max * 0.95)

        # Zonas de fundo do arco: verde=normal, amarelo=caution, vermelho=warning
        if variable in _MIN_LIMIT_VARS:
            steps = [
                dict(range=[v_min,      warning_val], color="#2A1515"),  # danger
                dict(range=[warning_val, caution_val], color="#2A2210"),  # caution
                dict(range=[caution_val, v_max],       color="#152A15"),  # normal
            ]
            threshold_value = caution_val
        else:
            steps = [
                dict(range=[v_min,      caution_val],  color="#152A15"),  # normal
                dict(range=[caution_val, warning_val], color="#2A2210"),  # caution
                dict(range=[warning_val, v_max],        color="#2A1515"),  # danger
            ]
            threshold_value = warning_val

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=safe_value,
            title=dict(
                text=label,
                font=dict(color="#AAAAAA", size=9, family="monospace"),
            ),
            number=dict(
                font=dict(color=bar_color, size=13, family="monospace"),
                suffix=f" {spec['unit']}",
            ),
            gauge=dict(
                axis=dict(
                    range=[v_min, v_max],
                    tickcolor="#444444",
                    tickfont=dict(color="#444444", size=7),
                    nticks=5,
                ),
                bar=dict(color=bar_color, thickness=0.28),
                bgcolor="#111111",
                borderwidth=1,
                bordercolor="#2D2D2D",
                steps=steps,
                threshold=dict(
                    line=dict(color="#FF4B4B", width=2),
                    thickness=0.80,
                    value=threshold_value,
                ),
            ),
        ))

        fig.update_layout(
            paper_bgcolor=COLORS["background"],
            plot_bgcolor=COLORS["background"],
            margin=dict(l=8, r=8, t=28, b=5),
            height=160,
        )

        return fig

    def plot_all_engine_gauges(self, snapshot: pd.Series) -> list[go.Figure]:
        """Gera a lista completa de 7 gauges para o snapshot temporal atual.

        Ordem: Q, ITT, NP, NG, FF, OT, OP
        """
        order = [("Q", "TORQUE"), ("ITT", "ITT"), ("NP", "Np"), ("NG", "Ng"),
                 ("FF", "F.FLOW"), ("OT", "OIL TEMP"), ("OP", "OIL PRESS")]

        def _safe(key: str) -> float:
            val = snapshot.get(key, 0)
            try:
                f = float(val)
                return f if f == f else 0.0
            except Exception:
                return 0.0

        return [self.plot_gauge(_safe(var), var, lbl) for var, lbl in order]
