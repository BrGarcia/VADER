"""
data_loader.py
Responsável pela ingestão de arquivos CSV do VADR, limpeza, tipagem
e conversão para Parquet (cache binário colunar).
"""

from __future__ import annotations

import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


class DataLoader:
    """Gerencia o ciclo de vida dos dados: CSV bruto → Parquet processado → DataFrame."""

    RAW_DIR: str = "data/raw"
    PROCESSED_DIR: str = "data/processed"

    # Colunas críticas esperadas no CSV (Fase 1)
    CORE_COLUMNS: list[str] = [
        "TIME", "STIME", "BALT", "PALT", "MACH", "AS",
        "AOA", "APA", "ARA", "NZ", "WOW", "LDG",
    ]

    def __init__(self, raw_dir: str = RAW_DIR, processed_dir: str = PROCESSED_DIR) -> None:
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir

    # ------------------------------------------------------------------
    # Ingestão
    # ------------------------------------------------------------------

    def ingest(self, filepath: str) -> pd.DataFrame:
        """Pipeline principal: lê CSV, limpa e converte para Parquet se necessário.

        Retorna o DataFrame processado pronto para uso na UI.
        """
        ...

    def _strip_metadata_headers(self, filepath: str, max_header_rows: int = 10) -> int:
        """Detecta e retorna o índice da linha onde os dados tabulares realmente começam.

        O CSV do VADR possui linhas de metadados antes do cabeçalho de colunas.
        """
        ...

    def _read_raw_csv(self, filepath: str) -> pd.DataFrame:
        """Lê o arquivo CSV pulando as linhas de metadados identificadas."""
        ...

    def _coerce_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converte colunas para os tipos corretos (float, int, datetime).

        Trata NaN e valores corrompidos sem lançar exceção.
        """
        ...

    def _resolve_time_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Garante que exista uma coluna 'TIME' como índice temporal do DataFrame.

        Suporta tanto 'TIME' quanto 'STIME' (aliases comuns no VADR).
        """
        ...

    # ------------------------------------------------------------------
    # Cache Parquet
    # ------------------------------------------------------------------

    def convert_to_parquet(self, df: pd.DataFrame, parquet_path: str) -> None:
        """Serializa o DataFrame para o formato Parquet na pasta processed/."""
        ...

    def load_parquet(self, parquet_path: str) -> pd.DataFrame:
        """Lê um arquivo Parquet previamente processado e retorna o DataFrame."""
        ...

    def _get_parquet_path(self, csv_filepath: str) -> str:
        """Calcula o caminho .parquet correspondente a um arquivo .csv."""
        ...

    def _parquet_is_fresh(self, csv_filepath: str, parquet_path: str) -> bool:
        """Verifica se o Parquet existe e é mais recente que o CSV de origem."""
        ...

    # ------------------------------------------------------------------
    # Utilitários de DataFrame
    # ------------------------------------------------------------------

    def get_numeric_columns(self, df: pd.DataFrame) -> list[str]:
        """Retorna lista de colunas numéricas disponíveis para plotagem no Eixo Y."""
        ...

    def get_row_at_time(self, df: pd.DataFrame, time_index: int) -> pd.Series:
        """Retorna a linha (snapshot) do DataFrame no índice temporal fornecido."""
        ...

    def get_fault_columns(self, df: pd.DataFrame) -> list[str]:
        """Retorna colunas com prefixo MW1_, MW2_, MW3_ presentes no DataFrame."""
        ...
