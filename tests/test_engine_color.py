"""
test_engine_color.py — Testa a função get_engine_color centralizada (DUP-04).
"""
from src.ui.plots import get_engine_color, COLORS


def test_normal_torque():
    assert get_engine_color(50.0, "Q") == COLORS["normal"]


def test_caution_itt():
    assert get_engine_color(860.0, "ITT") == COLORS["caution"]


def test_warning_itt():
    assert get_engine_color(1020.0, "ITT") == COLORS["warning"]


def test_oil_pressure_low_warning():
    """OP tem limite mínimo — abaixo é warning."""
    assert get_engine_color(10.0, "OP") == COLORS["warning"]


def test_oil_pressure_normal():
    assert get_engine_color(80.0, "OP") == COLORS["normal"]


def test_unknown_variable():
    assert get_engine_color(999.0, "UNKNOWN_VAR") == COLORS["normal"]
