import streamlit as st


class FaultPanel:

    COLORS = {
        "WARNING": "#ff1a1a",   # vermelho
        "CAUTION": "#ffff00",   # amarelo
        "ADVISORY": "#00bfff",  # azul
    }

    def render(self, faults: list[dict]):
        """
        Renderiza um grid denso de alertas (até 60) como um único bloco HTML.
        """

        # Início do container principal (6 colunas sugeridas para 60 alertas)
        html_grid = '<div style="height: 320px; border: 1px solid #2D2D2D; border-radius: 8px; padding: 6px; background: #0E1117; display: flex; flex-wrap: wrap; align-content: flex-start; gap: 4px; overflow: hidden;">'

        for fault in faults:
            active = fault.get("active", True)
            color = self.COLORS.get(fault["level"], "#444")
            bg_color = color if active else "black"
            text_color = "black" if active else color
            opacity = "1.0" if active else "0.2"

            # Grid de 6 colunas (width: calc(16.6% - gap))
            html_grid += (
                f'<div style="background-color: {bg_color}; color: {text_color}; font-weight: bold; '
                f'text-align: center; padding: 1px; border-radius: 2px; border: 1px solid {color}; '
                f'font-size: 0.7rem; opacity: {opacity}; width: calc(16.66% - 4px); min-height: 27px; '
                f'display: flex; align-items: center; justify-content: center; text-transform: uppercase; '
                f'box-sizing: border-box; line-height: 1.1;">{fault["name"]}</div>'
            )

        html_grid += '</div>'

        # Renderiza tudo de uma vez
        st.markdown(html_grid, unsafe_allow_html=True)