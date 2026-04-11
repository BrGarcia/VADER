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

    # Colunas críticas: sensores atualizam em sub-taxas, gerando células vazias.
    # Aplicamos forward-fill para manter o último valor conhecido até a próxima atualização.
    CORE_COLUMNS: list[str] = [
        "BALT", "PALT", "MACH", "AS",
        "AOA", "APA", "ARA", "NZ", "WOW", "LDG",
        "Q", "ITT", "NG", "NP", "FF", "OT", "OP",
    ]

    def __init__(self, raw_dir: str = RAW_DIR, processed_dir: str = PROCESSED_DIR) -> None:
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir

    # ------------------------------------------------------------------
    # Ingestão — pipeline principal
    # ------------------------------------------------------------------

    def ingest(self, filepath: str) -> pd.DataFrame:
        """Pipeline principal: lê CSV, extrai metadados, limpa e converte para Parquet se necessário.

        Retorna o DataFrame processado pronto para uso na UI.
        """
        parquet_path = self._get_parquet_path(filepath)
        metadata = self._extract_metadata(filepath)

        if self._parquet_is_fresh(filepath, parquet_path):
            df = self.load_parquet(parquet_path)
            df.attrs["metadata"] = metadata
            return df

        df = self._read_raw_csv(filepath)
        df = self._resolve_time_column(df)
        df = self._coerce_types(df)
        df = df.reset_index(drop=True)
        df.attrs["metadata"] = metadata

        self.convert_to_parquet(df, parquet_path)
        return df

    def _extract_metadata(self, filepath: str, max_header_rows: int = 8) -> dict[str, str]:
        """Extrai pares chave-valor das primeiras linhas de metadados do VADR.

        S-04 (extensão): também lê as colunas de relógio interno VADR
        (VADR_HOURS, VADR_MINUTES, VADR_SECOND, VADR_DAY, VADR_MONTH, VADR_YEAR)
        e a hora GPS real (GMT_HOUR, GMT_MIN, GMT_SEC) do primeiro registro de dados
        para calcular hora de início de voo e desvio de relógio.
        """
        meta = {}
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh):
                    if i >= max_header_rows: break
                    if "," in line:
                        parts = line.split(",", 1)
                        key = parts[0].strip()
                        val = parts[1].strip()
                        if key and val and "TIME" not in key:
                            meta[key] = val
        except Exception:
            pass

        # S-04: extrai timestamps VADR / GMT do primeiro registro de dados
        try:
            header_row = self._strip_metadata_headers(filepath)
            skip_rows = list(range(header_row)) + [header_row + 1]
            import pandas as _pd
            df_tmp = _pd.read_csv(
                filepath, skiprows=skip_rows, header=0,
                low_memory=False, nrows=1,
                na_values=["", " "], keep_default_na=True,
            )
            df_tmp.columns = [c.strip() for c in df_tmp.columns]

            # Hora interna do VADR
            vadr_cols = ["VADR_HOURS", "VADR_MINUTES", "VADR_SECOND",
                         "VADR_DAY", "VADR_MONTH", "VADR_YEAR"]
            if all(c in df_tmp.columns for c in vadr_cols):
                row = df_tmp.iloc[0]
                h, m, s = int(row["VADR_HOURS"]), int(row["VADR_MINUTES"]), int(row["VADR_SECOND"])
                d, mo, y = int(row["VADR_DAY"]), int(row["VADR_MONTH"]), int(row["VADR_YEAR"])
                meta["VADR Clock (1º reg.)"] = f"{d:02d}/{mo:02d}/{y:04d} {h:02d}:{m:02d}:{s:02d}"

            # Hora real GPS (GMT)
            gmt_cols = ["GMT_HOUR", "GMT_MIN", "GMT_SEC"]
            if all(c in df_tmp.columns for c in gmt_cols):
                row = df_tmp.iloc[0]
                gh, gm, gs = int(row["GMT_HOUR"]), int(row["GMT_MIN"]), int(row["GMT_SEC"])
                meta["GPS GMT (1º reg.)"] = f"{gh:02d}:{gm:02d}:{gs:02d} UTC"

                # Desvio entre relógio interno VADR e GPS real
                if "VADR_HOURS" in df_tmp.columns:
                    row = df_tmp.iloc[0]
                    vadr_secs = int(row["VADR_HOURS"]) * 3600 + int(row["VADR_MINUTES"]) * 60 + int(row["VADR_SECOND"])
                    gmt_secs  = gh * 3600 + gm * 60 + gs
                    drift_s   = gmt_secs - vadr_secs
                    meta["Δ Clock (GPS-VADR)"] = f"{drift_s:+d} s"
        except Exception:
            pass

        return meta

    def _strip_metadata_headers(self, filepath: str, max_header_rows: int = 15) -> int:
        """Detecta e retorna o índice da linha onde o cabeçalho tabular começa.

        S-04: procura por 'TIME' OU 'STIME' (robusto para todos os formatos VADR),
        dispensando a dependência de 'Rec' que nem sempre está presente.
        """
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= max_header_rows:
                    break
                # Aceita TIME ou STIME como marcador de cabeçalho tabular
                if "TIME" in line or "STIME" in line:
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
        """Converte colunas para numérico, aplica forward-fill e calcula coluna PHASE.

        S-05: a coluna 'PHASE' («ground» / «flight») é derivada do sensor WOW
        e gravada no Parquet para que TimelinePlotter.add_phase_bands() a leia
        diretamente, sem recalcular a cada rerun do Streamlit.
        """
        protected = {"TIME", "STIME", "TIME_STR"}

        for col in df.columns:
            if col in protected:
                continue
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Forward-fill colunas críticas
        cols_to_fill = [c for c in self.CORE_COLUMNS if c in df.columns]
        if cols_to_fill:
            df[cols_to_fill] = df[cols_to_fill].ffill()

        # S-05: pré-computa a coluna PHASE no momento da ingestão
        if "WOW" in df.columns:
            df["PHASE"] = (
                df["WOW"].astype(float).fillna(0).astype(int)
                .map({1: "ground", 0: "flight"})
                .fillna("flight")
            )

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
