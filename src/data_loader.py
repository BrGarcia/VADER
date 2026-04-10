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

    # Colunas críticas da Fase 1 — forward-fill aplicado a todas
    CORE_COLUMNS: list[str] = [
        "BALT", "PALT", "MACH", "AS",
        "AOA", "APA", "ARA", "NZ", "WOW", "LDG",
    ]

    def __init__(self, raw_dir: str = RAW_DIR, processed_dir: str = PROCESSED_DIR) -> None:
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir

    # ------------------------------------------------------------------
    # Ingestão — pipeline principal
    # ------------------------------------------------------------------

    def ingest(self, filepath: str) -> pd.DataFrame:
        """Pipeline principal: lê CSV, limpa e converte para Parquet se necessário.

        Retorna o DataFrame processado pronto para uso na UI.
        """
        parquet_path = self._get_parquet_path(filepath)

        if self._parquet_is_fresh(filepath, parquet_path):
            return self.load_parquet(parquet_path)

        df = self._read_raw_csv(filepath)
        df = self._resolve_time_column(df)
        df = self._coerce_types(df)
        df = df.reset_index(drop=True)

        self.convert_to_parquet(df, parquet_path)
        return df

    def _strip_metadata_headers(self, filepath: str, max_header_rows: int = 15) -> int:
        """Detecta e retorna o índice da linha onde o cabeçalho tabular começa.

        Varre até max_header_rows linhas procurando a que contém 'TIME' e 'Rec',
        que é a linha de cabeçalho de colunas do VADR.
        """
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= max_header_rows:
                    break
                if "TIME" in line and "Rec" in line:
                    return i
        return 8  # fallback seguro para o formato VADR padrão

    def _read_raw_csv(self, filepath: str) -> pd.DataFrame:
        """Lê o arquivo CSV pulando metadados e a linha de unidades."""
        header_row = self._strip_metadata_headers(filepath)
        # A linha logo após o cabeçalho contém as unidades (ex: "HH:MM:SS.FFF, degrees...")
        # e não deve ser interpretada como dado.
        skip_rows = list(range(header_row)) + [header_row + 1]

        df = pd.read_csv(
            filepath,
            skiprows=skip_rows,
            header=0,
            low_memory=False,
            na_values=["", " "],
            keep_default_na=True,
        )
        # Limpa espaços em branco nos nomes das colunas
        df.columns = [c.strip() for c in df.columns]
        return df

    def _coerce_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converte colunas para numérico e aplica forward-fill nas colunas de voo.

        Colunas TIME_STR e TIME são preservadas; todas as demais recebem
        pd.to_numeric(errors='coerce') para tratar valores inválidos sem falhar.
        """
        protected = {"TIME", "STIME", "TIME_STR"}

        for col in df.columns:
            if col in protected:
                continue
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Forward-fill colunas críticas: sensores atualizam em sub-taxas, gerando
        # células vazias nas linhas intermediárias.
        cols_to_fill = [c for c in self.CORE_COLUMNS if c in df.columns]
        if cols_to_fill:
            df[cols_to_fill] = df[cols_to_fill].ffill()

        return df

    def _resolve_time_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza a coluna de tempo para segundos decorridos desde o início.

        Suporta os formatos 'TIME' e 'STIME' (HH:MM:SS.FFF).
        Cria 'TIME_STR' com o valor original para exibição no slider.
        """
        time_col = "TIME" if "TIME" in df.columns else "STIME" if "STIME" in df.columns else None

        if time_col is None:
            # Fallback: assume 8 Hz
            df["TIME"] = df.index * 0.125
            df["TIME_STR"] = df["TIME"].apply(lambda s: f"{s:.3f}s")
            return df

        def _hms_to_seconds(value: str) -> float:
            try:
                parts = str(value).split(":")
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            except Exception:
                return float("nan")

        elapsed = df[time_col].apply(_hms_to_seconds)
        t_min = elapsed.min()
        elapsed = elapsed - t_min

        df["TIME_STR"] = df[time_col].astype(str)
        df["TIME"] = elapsed

        return df

    # ------------------------------------------------------------------
    # Cache Parquet
    # ------------------------------------------------------------------

    def convert_to_parquet(self, df: pd.DataFrame, parquet_path: str) -> None:
        """Serializa o DataFrame para Parquet na pasta processed/."""
        os.makedirs(os.path.dirname(os.path.abspath(parquet_path)), exist_ok=True)
        table = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_table(table, parquet_path, compression="snappy")

    def load_parquet(self, parquet_path: str) -> pd.DataFrame:
        """Lê um arquivo Parquet previamente processado."""
        df = pq.read_table(parquet_path).to_pandas()
        df.columns = [c.strip() for c in df.columns]
        return df

    def _get_parquet_path(self, csv_filepath: str) -> str:
        """Calcula o caminho .parquet correspondente ao csv fornecido."""
        basename = os.path.splitext(os.path.basename(csv_filepath))[0]
        return os.path.join(self.processed_dir, f"{basename}.parquet")

    def _parquet_is_fresh(self, csv_filepath: str, parquet_path: str) -> bool:
        """Retorna True se o Parquet existe e é mais recente que o CSV de origem."""
        if not os.path.exists(parquet_path):
            return False
        return os.path.getmtime(parquet_path) >= os.path.getmtime(csv_filepath)

    # ------------------------------------------------------------------
    # Utilitários de DataFrame
    # ------------------------------------------------------------------

    def get_numeric_columns(self, df: pd.DataFrame) -> list[str]:
        """Retorna colunas numéricas de dados, excluindo flags de validade e TIME."""
        numeric = df.select_dtypes(include="number").columns.tolist()
        col_set = set(df.columns)
        excluded = {"TIME", "Rec #", "Rec"}

        # Colunas de validade seguem o padrão XYZV onde XYZ é o nome do dado.
        validity_cols = {
            c for c in numeric
            if c.endswith("V") and len(c) > 1 and c[:-1] in col_set
        }

        result = [c for c in numeric if c not in excluded and c not in validity_cols]
        return sorted(result)

    def get_row_at_time(self, df: pd.DataFrame, time_index: int) -> pd.Series:
        """Retorna a linha (snapshot) do DataFrame no índice temporal fornecido."""
        idx = max(0, min(time_index, len(df) - 1))
        return df.iloc[idx]

    def get_fault_columns(self, df: pd.DataFrame) -> list[str]:
        """Retorna colunas com prefixo MW1_, MW2_, MW3_ presentes no DataFrame."""
        return [c for c in df.columns if c.startswith(("MW1_", "MW2_", "MW3_"))]
