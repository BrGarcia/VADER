"""
dtc_parser.py
Módulo responsável pela leitura e consolidação dos arquivos binários de falha
do DTC (Pitch Trim Switch Monitor - TRIMM*.DMP).
Integra a lógica do script conversor original ao ecossistema do VADER.
"""

import os
import pandas as pd
from pathlib import Path

class DtcParser:
    """Classe para leitura e processamento de arquivos TRIMM*.DMP do DTC."""

    COLUNAS_TRIMM = [
        "UTC", "Emer_ON", "Emer_SW", "Stick_FWD", "Stick_AFT", 
        "CAS", "TAS", "GS", "BARO", "RALT", "PITCH_ANG", 
        "ROLL_ANG", "AIL_T_POS", "ELEV_T_POS", "RUD_T_POS", 
        "PITCH_MIS", "ROLL_MIS", "Yellow_Zone", "Descarte_Delimitador"
    ]

    @staticmethod
    def localizar_arquivos(diretorio: str) -> list[Path]:
        """Retorna a lista ordenada de arquivos TRIMM*.DMP no diretório fornecido."""
        path = Path(diretorio)
        return sorted(path.glob("TRIMM*.DMP"))

    @classmethod
    def ler_arquivo(cls, caminho_arquivo: str | Path) -> pd.DataFrame:
        """Lê um único arquivo DMP, nomeia as colunas e adiciona a origem."""
        caminho = Path(caminho_arquivo)
        try:
            df = pd.read_csv(
                caminho, 
                sep=";", 
                header=None, 
                names=cls.COLUNAS_TRIMM, 
                index_col=False,
                on_bad_lines='skip'
            )
            
            if "Descarte_Delimitador" in df.columns:
                df = df.drop(columns=["Descarte_Delimitador"])
                
            df.insert(0, "Origem_Arquivo", caminho.name)
            return df
        except Exception as e:
            print(f"Erro ao ler {caminho.name}: {e}")
            return pd.DataFrame()

    @classmethod
    def processar_diretorio(cls, diretorio: str) -> pd.DataFrame:
        """Lê e consolida todos os arquivos TRIMM da pasta especificada no disco."""
        arquivos = cls.localizar_arquivos(diretorio)
        if not arquivos:
            return pd.DataFrame()
            
        lista_dfs = [cls.ler_arquivo(arq) for arq in arquivos]
        return cls._consolidar(lista_dfs, len(arquivos))

    @classmethod
    def ingest_files(cls, uploaded_files: list) -> pd.DataFrame:
        """Processa uma lista de arquivos em memória (ex: UploadedFile do Streamlit)."""
        lista_dfs = []
        for uf in uploaded_files:
            try:
                df = pd.read_csv(
                    uf, 
                    sep=";", 
                    header=None, 
                    names=cls.COLUNAS_TRIMM, 
                    index_col=False,
                    on_bad_lines='skip'
                )
                if "Descarte_Delimitador" in df.columns:
                    df = df.drop(columns=["Descarte_Delimitador"])
                df.insert(0, "Origem_Arquivo", uf.name)
                if not df.empty:
                    lista_dfs.append(df)
            except Exception as e:
                print(f"Erro ao ler arquivo em memória {uf.name}: {e}")
                
        return cls._consolidar(lista_dfs, len(uploaded_files))

    @classmethod
    def _consolidar(cls, lista_dfs: list[pd.DataFrame], qtd_arquivos: int) -> pd.DataFrame:
        """Aplica a conversão de tempo e gera as flags de disparo."""
        lista_dfs = [df for df in lista_dfs if not df.empty]
        if not lista_dfs:
            return pd.DataFrame()
            
        df_final = pd.concat(lista_dfs, ignore_index=True)
        
        # 1. Converter UTC para formatação string 'HH:MM:SS.FFF' e criar coluna TIME
        horas_formatadas = pd.to_datetime(df_final["UTC"], unit='ms').dt.strftime('%H:%M:%S.%f')
        horas_formatadas = horas_formatadas.str[:-3]
        
        if "Hora" not in df_final.columns:
            df_final.insert(2, "Hora", horas_formatadas)
            
        # Converter milissegundos para segundos decorridos para padronizar com VADR
        t_min = df_final["UTC"].min()
        df_final["TIME"] = (df_final["UTC"] - t_min) / 1000.0
        df_final["TIME_STR"] = horas_formatadas
        
        # 2. Calcular Threshold_ms
        threshold_ms = 0
        if len(df_final) >= 2:
            threshold_ms = (df_final["UTC"].iloc[1] - df_final["UTC"].iloc[0]) * 2
            
        # 3. Detectar Atuações Não Comandadas
        diff_utc = df_final["UTC"].shift(-1) - df_final["UTC"]
        condicao_tempo = diff_utc > threshold_ms
        
        # Aileron_Test
        diff_ail = (df_final["AIL_T_POS"] - df_final["AIL_T_POS"].shift(-1)).abs()
        condicao_aileron = condicao_tempo & (diff_ail > 1)
        df_final["Aileron_Test"] = condicao_aileron.astype(int)
        
        # Elevator_Test
        diff_elev = (df_final["ELEV_T_POS"] - df_final["ELEV_T_POS"].shift(-1)).abs()
        condicao_elevator = condicao_tempo & (diff_elev > 1)
        df_final["Elevator_Test"] = condicao_elevator.astype(int)
        
        # Salvar metadata no DataFrame
        aileron_count = int(df_final["Aileron_Test"].sum())
        elevator_count = int(df_final["Elevator_Test"].sum())
        
        df_final.attrs["metadata"] = {
            "Total de Arquivos": qtd_arquivos,
            "Total de Registros": len(df_final),
            "Threshold (ms)": threshold_ms,
            "Disparos Aileron": aileron_count,
            "Disparos Elevator": elevator_count,
            "Status": "🚨 SUSPEITA DE DISPARO" if (aileron_count > 0 or elevator_count > 0) else "✅ NORMAL"
        }
        
        return df_final
