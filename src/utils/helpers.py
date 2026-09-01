"""
helpers.py
Funções utilitárias compartilhadas do V.A.D.E.R.
DUP-01: centraliza a função _safe() que estava duplicada em 4 módulos.
"""

from __future__ import annotations


def safe_numeric(source, key: str, fallback: float = 0.0) -> float:
    """Lê um valor numérico de um pd.Series/dict com tratamento de NaN e erros.

    Args:
        source: pd.Series ou dict-like com método .get()
        key: nome da chave/coluna
        fallback: valor padrão se ausente, inválido ou NaN

    Returns:
        Valor float válido, ou fallback.
    """
    val = source.get(key, fallback)
    try:
        f = float(val)
        return f if f == f else fallback  # NaN check: NaN != NaN
    except (ValueError, TypeError):
        return fallback
