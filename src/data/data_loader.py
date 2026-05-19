"""
data_loader.py
Responsável pela ingestão de arquivos CSV do VADR, limpeza, tipagem
e conversão para Parquet (cache binário colunar).
"""

from __future__ import annotations

import json
import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


class DataLoader:
    """Gerencia o ciclo de vida dos dados: CSV bruto → Parquet processado → DataFrame."""

    RAW_DIR: str = "data/raw"
    PROCESSED_DIR: str = "data/processed"

    # A.6 — Variáveis carregadas no modo "basic" (28 colunas originais do CSV).
    # Colunas derivadas internas (TIME_STR, PHASE) são criadas no pipeline
    # e não precisam estar no CSV bruto.
    BASIC_ANALYSIS_COLUMNS: list[str] = [
        "TIME", "STIME",
        "GPSLAT", "GPSLONG",
        "BALT", "PALT", "RAD_ALT", "MACH", "AOA", "APA", "ARA", "NZ", "MAG_HDG",
        "WOW", "LDG", "FLAP", "AIRBRK",
        "PCL", "Q", "ITT", "NG", "NP", "FF", "OT", "OP",
        "ENGFIRE", "MWC_DATA", "VALIDARINC", "FR",
    ]

    # Colunas críticas: sensores atualizam em sub-taxas, gerando células vazias.
    # Aplicamos forward-fill para manter o último valor conhecido até a próxima atualização.
    CORE_COLUMNS: list[str] = [
        "BALT", "PALT", "MACH", "AS",
        "AOA", "APA", "ARA", "NZ", "WOW", "LDG",
        "Q", "ITT", "NG", "NP", "FF", "OT", "OP",
        "PCL", "MWC_DATA",
    ]

    def __init__(self, raw_dir: str = RAW_DIR, processed_dir: str = PROCESSED_DIR) -> None:
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir

    # ------------------------------------------------------------------
    # Ingestão — pipeline principal
    # ------------------------------------------------------------------

    def ingest(self, filepath: str, analysis_mode: str = "complete") -> pd.DataFrame:
        """Pipeline principal: lê CSV, extrai metadados, limpa e converte para Parquet se necessário.

        Args:
            filepath: Caminho para o arquivo CSV bruto.
            analysis_mode: ``"basic"`` carrega apenas as 28 variáveis essenciais;
                ``"complete"`` carrega todas as colunas do CSV (padrão anterior).

        Retorna o DataFrame processado pronto para uso na UI.
        """
        parquet_path = self._get_parquet_path(filepath, analysis_mode)
        meta_path = self._get_meta_path(parquet_path)

        if self._parquet_is_fresh(filepath, parquet_path):
            df = self.load_parquet(parquet_path)
            # BUG-05: carrega metadata do JSON sidecar (persiste sem CSV)
            df.attrs["metadata"] = self._load_metadata_json(meta_path, filepath)
            df.attrs["analysis_mode"] = analysis_mode
            return df

        metadata = self._extract_metadata(filepath)
        df = self._read_raw_csv(filepath, analysis_mode)
        df = self._resolve_time_column(df)
        df = self._coerce_types(df)
        df = df.reset_index(drop=True)
        df.attrs["metadata"] = metadata
        df.attrs["analysis_mode"] = analysis_mode

        self.convert_to_parquet(df, parquet_path)
        # BUG-05: salva metadata como JSON sidecar
        self._save_metadata_json(meta_path, metadata)
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

    def _read_raw_csv(self, filepath: str, analysis_mode: str = "complete") -> pd.DataFrame:
        """Lê o arquivo CSV pulando metadados e a linha de unidades.

        A.6 — No modo ``"basic"``, passa ``usecols`` ao ``read_csv`` para carregar
        apenas as 28 variáveis essenciais, reduzindo parsing, memória e tempo de
        ingestão sem precisar filtrar depois.
        """
        header_row = self._strip_metadata_headers(filepath)
        # A linha logo após o cabeçalho contém as unidades (ex: "HH:MM:SS.FFF, degrees...")
        # e não deve ser interpretada como dado.
        skip_rows = list(range(header_row)) + [header_row + 1]

        # A.6 — filtra colunas já no read_csv para o modo básico
        if analysis_mode == "basic":
            basic_set = set(self.BASIC_ANALYSIS_COLUMNS)
            usecols_fn = lambda c: c.strip() in basic_set  # noqa: E731
        else:
            usecols_fn = None

        df = pd.read_csv(
            filepath,
            skiprows=skip_rows,
            header=0,
            usecols=usecols_fn,
            low_memory=False,
            na_values=["", " "],
            keep_default_na=True,
        )
        # Limpa espaços em branco nos nomes das colunas
        df.columns = [c.strip() for c in df.columns]

        # IMP-09: valida estrutura mínima do CSV
        if "TIME" not in df.columns and "STIME" not in df.columns:
            raise ValueError(
                f"CSV inválido: coluna TIME ou STIME não encontrada. "
                f"Colunas disponíveis: {list(df.columns)[:10]}"
            )

        return df

    def _coerce_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converte colunas para numérico, aplica forward-fill e calcula coluna PHASE.

        S-05: a coluna 'PHASE' («ground» / «flight») é derivada do sensor WOW
        e gravada no Parquet para que TimelinePlotter.add_phase_bands() a leia
        diretamente, sem recalcular a cada rerun do Streamlit.

        Usa pd.concat para converter todas as colunas numéricas de uma única vez,
        evitando o PerformanceWarning de DataFrame fragmentado que ocorria com o
        loop de atribuições individuais (frame[col] = ...).
        """
        protected = {"TIME", "STIME", "TIME_STR"}
        numeric_cols = [c for c in df.columns if c not in protected]
        protected_cols = [c for c in df.columns if c in protected]

        # Converte todas as colunas não protegidas de uma só vez (evita fragmentação)
        numeric_converted = df[numeric_cols].apply(
            lambda s: pd.to_numeric(s, errors="coerce")
        )

        # Reconstrói o DataFrame de forma coesa (sem fragmentação interna)
        df = pd.concat([df[protected_cols], numeric_converted], axis=1)[df.columns]

        # Forward-fill colunas críticas
        cols_to_fill = [c for c in self.CORE_COLUMNS if c in df.columns]
        if cols_to_fill:
            df[cols_to_fill] = df[cols_to_fill].ffill()

        # S-05: pré-computa a coluna PHASE no momento da ingestão
        if "WOW" in df.columns:
            phase = (
                df["WOW"].astype(float).fillna(0).astype(int)
                .map({1: "ground", 0: "flight"})
                .fillna("flight")
            )
            df = pd.concat([df, phase.rename("PHASE")], axis=1)

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

        # Garante que colunas object com tipos mistos (ex: CAS) são convertidas para float
        # antes da serialização Arrow — evita ArrowTypeError em colunas ambíguas
        protected = {"TIME_STR", "PHASE"}
        df_clean = df.copy()
        for col in df_clean.columns:
            if col in protected:
                continue
            if df_clean[col].dtype == object:
                df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

        table = pa.Table.from_pandas(df_clean, preserve_index=False)
        pq.write_table(table, parquet_path, compression="snappy")

    def load_parquet(self, parquet_path: str) -> pd.DataFrame:
        """Lê um arquivo Parquet previamente processado."""
        df = pq.read_table(parquet_path).to_pandas()
        df.columns = [c.strip() for c in df.columns]
        return df

    def _get_parquet_path(self, csv_filepath: str, analysis_mode: str = "complete") -> str:
        """Calcula o caminho .parquet correspondente ao csv e ao modo de análise.

        A.6 — O sufixo ``__basic`` / ``__complete`` evita conflito entre os
        dois Parquets gerados para o mesmo CSV.
        """
        basename = os.path.splitext(os.path.basename(csv_filepath))[0]
        return os.path.join(self.processed_dir, f"{basename}__{analysis_mode}.parquet")

    def _parquet_is_fresh(self, csv_filepath: str, parquet_path: str) -> bool:
        """Retorna True se o Parquet existe e é mais recente que o CSV de origem."""
        if not os.path.exists(parquet_path):
            return False
        return os.path.getmtime(parquet_path) >= os.path.getmtime(csv_filepath)

    @staticmethod
    def _get_meta_path(parquet_path: str) -> str:
        """Calcula o caminho .meta.json correspondente ao Parquet."""
        return parquet_path.replace(".parquet", ".meta.json")

    @staticmethod
    def _save_metadata_json(meta_path: str, metadata: dict) -> None:
        """Salva metadata como JSON sidecar ao lado do Parquet."""
        try:
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # Não bloqueia pipeline por falha de metadata

    def _load_metadata_json(self, meta_path: str, csv_filepath: str) -> dict:
        """Carrega metadata do JSON sidecar. Fallback para re-extração do CSV."""
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # Fallback: re-extrai do CSV se disponível
        if os.path.exists(csv_filepath):
            return self._extract_metadata(csv_filepath)
        return {}

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
