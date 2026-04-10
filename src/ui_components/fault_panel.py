import streamlit as st


class FaultPanel:

    COLORS = {
        "WARNING": "#ff1a1a",   # vermelho
        "CAUTION": "#ffff00",   # amarelo
        "ADVISORY": "#00bfff",  # azul
    }

    def _render_box(self, text, level):
        color = self.COLORS.get(level, "#444")

        html = f"""
        <div style="
            background-color: {color};
            color: black;
            font-weight: bold;
            text-align: center;
            padding: 12px;
            border-radius: 6px;
            border: 3px solid {color};
            font-size: 18px;
            margin: 5px;
        ">
            {text}
        </div>
        """

        st.markdown(html, unsafe_allow_html=True)

    def render(self, faults: list[dict]):
        """
        faults = [
            {"name": "OIL PRES", "level": "WARNING"},
            {"name": "GEN", "level": "CAUTION"},
            {"name": "INERT SEP", "level": "ADVISORY"},
        ]
        """

        cols = st.columns(4)

        for i, fault in enumerate(faults):
            with cols[i % 4]:
                self._render_box(fault["name"], fault["level"])