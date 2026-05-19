import numpy as np
import plotly.graph_objects as go


class VerticalSpeedIndicator:
    def __init__(self, min_vsi=-3000, max_vsi=3000):
        self.min_vsi = min_vsi
        self.max_vsi = max_vsi

    def _value_to_angle(self, value):
        value = max(min(value, self.max_vsi), self.min_vsi)
        return (value / self.max_vsi) * 135

    def _create_ticks(self):
        shapes = []
        annotations = []

        for v in [-3000, -2000, -1000, 0, 1000, 2000, 3000]:
            angle = np.deg2rad(self._value_to_angle(v))

            r1 = 0.75
            r2 = 0.9

            x0 = 0.5 + r1 * np.sin(angle)
            y0 = 0.5 + r1 * np.cos(angle)

            x1 = 0.5 + r2 * np.sin(angle)
            y1 = 0.5 + r2 * np.cos(angle)

            shapes.append(dict(
                type="line",
                x0=x0, y0=y0,
                x1=x1, y1=y1,
                line=dict(color="white", width=2)
            ))

            if v != 0:
                label = str(abs(v // 1000))
                xt = 0.5 + (r1 - 0.1) * np.sin(angle)
                yt = 0.5 + (r1 - 0.1) * np.cos(angle)

                annotations.append(dict(
                    x=xt, y=yt,
                    text=label,
                    showarrow=False,
                    font=dict(color="white", size=12)
                ))

        return shapes, annotations

    def render(self, vsi_value):
        angle_deg = self._value_to_angle(vsi_value)
        angle_rad = np.deg2rad(angle_deg)

        needle_length = 0.7
        x_end = 0.5 + needle_length * np.sin(angle_rad)
        y_end = 0.5 + needle_length * np.cos(angle_rad)

        tick_shapes, tick_labels = self._create_ticks()

        fig = go.Figure()

        # Fundo
        fig.add_shape(
            type="circle",
            x0=0, y0=0,
            x1=1, y1=1,
            line=dict(color="white", width=2),
            fillcolor="black"
        )

        # Ticks
        for s in tick_shapes:
            fig.add_shape(s)

        # Ponteiro
        fig.add_shape(
            type="line",
            x0=0.5, y0=0.5,
            x1=x_end, y1=y_end,
            line=dict(color="white", width=4)
        )

        # Centro
        fig.add_shape(
            type="circle",
            x0=0.48, y0=0.48,
            x1=0.52, y1=0.52,
            fillcolor="white",
            line=dict(color="white")
        )

        fig.update_layout(
            annotations=tick_labels + [
                dict(
                    x=0.5, y=0.15,
                    text="VSI",
                    showarrow=False,
                    font=dict(color="white", size=14)
                ),
                dict(
                    x=0.5, y=0.08,
                    text="ft/min",
                    showarrow=False,
                    font=dict(color="gray", size=10)
                )
            ],
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            paper_bgcolor="black",
            margin=dict(l=10, r=10, t=10, b=10),
            height=300
        )

        return fig


# =========================================================
# 🔥 MODO DEMO (executar diretamente com Streamlit)
# =========================================================
if __name__ == "__main__":
    import streamlit as st

    st.set_page_config(layout="centered")

    st.title("✈️ Vertical Speed Indicator (VSI) - Demo")

    vsi = VerticalSpeedIndicator()

    # Slider para simular dados
    value = st.slider("VSI (ft/min)", -3000, 3000, 0, step=100)

    # Render
    fig = vsi.render(value)
    st.plotly_chart(fig, use_container_width=True)