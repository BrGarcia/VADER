"""
dtc_styles.py
Estilos de destaque compartilhados entre as views DTC (dtc.py) e completa.py,
para evitar a duplicacao de highlight_status_t/highlight_test_1/aplicar_estilos.
"""

from __future__ import annotations

import pandas as pd

COLS_STATUS_T = ["Emer_ON", "Emer_SW", "Stick_FWD", "Stick_AFT"]
COLS_TEST_1 = ["Aileron_Test", "Elevator_Test"]


def highlight_status_t(val) -> str:
    if str(val).strip().upper() == "T":
        return 'background-color: rgba(255, 152, 0, 0.4); color: white; font-weight: bold;'
    return ''


def highlight_test_1(val) -> str:
    if str(val).strip() == "1":
        return 'background-color: rgba(255, 75, 75, 0.5); color: white; font-weight: bold;'
    return ''


def aplicar_estilos(data_frame: pd.DataFrame):
    """Aplica os destaques de status (T) e disparo (1) a um DataFrame do DTC."""
    cols_t = [c for c in COLS_STATUS_T if c in data_frame.columns]
    cols_1 = [c for c in COLS_TEST_1 if c in data_frame.columns]

    styler = data_frame.style
    if hasattr(styler, "map"):
        styler = styler.map(highlight_status_t, subset=cols_t)
        styler = styler.map(highlight_test_1, subset=cols_1)
    else:
        styler = styler.applymap(highlight_status_t, subset=cols_t)
        styler = styler.applymap(highlight_test_1, subset=cols_1)
    return styler
