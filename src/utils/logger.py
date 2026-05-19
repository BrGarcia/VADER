"""
logger.py
Framework de logging centralizado do V.A.D.E.R.
IMP-01: substitui print() por logging estruturado.
"""

import logging
import sys

def get_logger(name: str = "vader") -> logging.Logger:
    """Retorna o logger configurado do VADER. Cria handler apenas na primeira chamada."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s — %(name)s — %(message)s", datefmt="%H:%M:%S")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
