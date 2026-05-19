"""
test_helpers.py — Testa a função safe_numeric centralizada (DUP-01).
"""
from src.utils.helpers import safe_numeric


def test_safe_numeric_normal():
    source = {"BALT": 15000.0, "MACH": 0.65}
    assert safe_numeric(source, "BALT") == 15000.0
    assert safe_numeric(source, "MACH") == 0.65


def test_safe_numeric_missing_key():
    source = {"BALT": 15000.0}
    assert safe_numeric(source, "MISSING") == 0.0
    assert safe_numeric(source, "MISSING", 99.9) == 99.9


def test_safe_numeric_nan():
    source = {"BALT": float("nan")}
    assert safe_numeric(source, "BALT") == 0.0
    assert safe_numeric(source, "BALT", -1.0) == -1.0


def test_safe_numeric_invalid_type():
    source = {"BALT": "texto_invalido"}
    assert safe_numeric(source, "BALT") == 0.0


def test_safe_numeric_string_number():
    source = {"BALT": "15000.5"}
    assert safe_numeric(source, "BALT") == 15000.5
