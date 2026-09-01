"""
dtc_styles.py
DUP-02: Estilos de tabela DTC centralizados (antes duplicados em dtc.py e completa.py).
"""

from __future__ import annotations

import pandas as pd
from pandas.io.formats.style import Styler


def _highlight_status_t(val) -> str:
    """Destaca células com valor 'T' (switches de emergência ativos)."""
    if str(val).strip().upper() == "T":
        return 'background-color: rgba(255, 152, 0, 0.4); color: white; font-weight: bold;'
    return ''


def _highlight_test_1(val) -> str:
    """Destaca células com valor '1' (testes de superfície disparados)."""
    if str(val).strip() == "1":
        return 'background-color: rgba(255, 75, 75, 0.5); color: white; font-weight: bold;'
    return ''


def aplicar_estilos_dtc(df: pd.DataFrame) -> Styler:
    """Aplica estilos padronizados de DTC ao DataFrame fornecido.

    Retorna um Styler pronto para exibição com st.dataframe().
    """
    cols_t = [c for c in ["Emer_ON", "Emer_SW", "Stick_FWD", "Stick_AFT"] if c in df.columns]
    cols_1 = [c for c in ["Aileron_Test", "Elevator_Test"] if c in df.columns]

    styler = df.style
    if hasattr(styler, "map"):
        styler = styler.map(_highlight_status_t, subset=cols_t)
        styler = styler.map(_highlight_test_1, subset=cols_1)
    else:
        styler = styler.applymap(_highlight_status_t, subset=cols_t)
        styler = styler.applymap(_highlight_test_1, subset=cols_1)
    return styler
