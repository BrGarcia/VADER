import streamlit as st


class FaultPanel:
    """Painel de alertas EICAS com efeito ghosting.

    Cada célula usa overflow:hidden + text-overflow:ellipsis (S-06) para
    evitar que labels longos quebrem o grid. O nome completo é acessível
    via tooltip nativo (atributo HTML title).
    """

    COLORS = {
        "WARNING":  "#ff1a1a",   # vermelho
        "CAUTION":  "#ffff00",   # amarelo
        "ADVISORY": "#00bfff",   # azul
    }

    def render(self, faults: list[dict]) -> None:
        """Renderiza um grid denso de alertas (até 60) como um único bloco HTML."""

        html_grid = (
            '<div style="height: 320px; border: 1px solid #2D2D2D; border-radius: 8px; '
            'padding: 6px; background: #0E1117; display: flex; flex-wrap: wrap; '
            'align-content: flex-start; gap: 4px; overflow: hidden;">'
        )

        for fault in faults:
            active    = fault.get("active", True)
            color     = self.COLORS.get(fault["level"], "#444")
            bg_color  = color if active else "black"
            txt_color = "black" if active else color
            opacity   = "1.0" if active else "0.2"
            # S-06: nome completo exposto como tooltip nativo
            full_name = fault["name"].replace('"', "&quot;")

            html_grid += (
                f'<div title="{full_name}" style="'
                f'background-color: {bg_color}; color: {txt_color}; font-weight: bold; '
                f'text-align: center; padding: 1px; border-radius: 2px; '
                f'border: 1px solid {color}; font-size: 0.7rem; opacity: {opacity}; '
                f'width: calc(16.66% - 4px); min-height: 27px; '
                f'display: flex; align-items: center; justify-content: center; '
                f'text-transform: uppercase; box-sizing: border-box; line-height: 1.1; '
                f'overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">'
                f'{fault["name"]}</div>'
            )

        html_grid += '</div>'
        st.markdown(html_grid, unsafe_allow_html=True)