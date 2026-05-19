"""
trimm_analysis.py
Módulo especializado em detectar atuações não comandadas nos dados TRIMM.
Verifica se há movimento de superfícies ou mudança de atitude sem comando nos manches.
"""

import pandas as pd
import numpy as np

class TrimmAnalyzer:
    """Analisa discrepâncias entre comandos (Stick) e resposta das superfícies/atitude."""

    def __init__(self, threshold_surface: float = 0.5, threshold_attitude: float = 0.2):
        """
        :param threshold_surface: Variação mínima na posição da superfície para considerar movimento (deg).
        :param threshold_attitude: Variação mínima na atitude para considerar movimento (deg/s ou delta).
        """
        self.threshold_surface = threshold_surface
        self.threshold_attitude = threshold_attitude

    def detect_uncommanded_motion(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adiciona colunas de flag para detectar movimento quando os manches estão em FALSE.
        
        Lógica:
        - Stick_Active = (Stick_FWD == TRUE) OR (Stick_AFT == TRUE)
        - Surface_Moving = Delta(AIL_T_POS) > threshold OR Delta(ELEV_T_POS) > threshold ...
        - Uncommanded = Surface_Moving AND (NOT Stick_Active)
        """
        # 1. Identifica se houve qualquer comando de manche
        # Stick_FWD e Stick_AFT já foram convertidos para 0/1 no trimm_converter
        df['STICK_ACTIVE'] = (df['Stick_FWD'] > 0) | (df['Stick_AFT'] > 0)

        # 2. Calcula variações (Deltas) para superfícies e atitude
        surfaces = ['AIL_T_POS', 'ELEV_T_POS', 'RUD_T_POS']
        attitudes = ['ROLL_ANG', 'PITCH_ANG']
        
        # Filtra apenas as que existem no DF
        available_surfaces = [c for c in surfaces if c in df.columns]
        available_attitudes = [c for c in attitudes if c in df.columns]

        # Delta absoluto entre registros consecutivos
        for col in available_surfaces + available_attitudes:
            # Garante que é numérico antes de fazer diff
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[f'DELTA_{col}'] = df[col].diff().abs().fillna(0)

        # 3. Detecta se houve movimento significativo
        df['SURFACE_MOVING'] = False
        for col in available_surfaces:
            df['SURFACE_MOVING'] |= (df[f'DELTA_{col}'] > self.threshold_surface)
            
        df['ATTITUDE_CHANGING'] = False
        for col in available_attitudes:
            df['ATTITUDE_CHANGING'] |= (df[f'DELTA_{col}'] > self.threshold_attitude)

        # 4. FLAG DE ATUAÇÃO NÃO COMANDADA
        # Atuação não comandada = (Movimento de Superfície OU Mudança de Atitude) E (Manche Inativo)
        df['UNCOMMANDED_ACT'] = (df['SURFACE_MOVING'] | df['ATTITUDE_CHANGING']) & (~df['STICK_ACTIVE'])
        
        # Especialização por eixo para facilitar plotagem
        if 'AIL_T_POS' in df.columns:
            df['UNC_ROLL'] = (df['DELTA_AIL_T_POS'] > self.threshold_surface) & (~df['STICK_ACTIVE'])
        if 'ELEV_T_POS' in df.columns:
            df['UNC_PITCH'] = (df['DELTA_ELEV_T_POS'] > self.threshold_surface) & (~df['STICK_ACTIVE'])
            
        return df

    def get_summary_report(self, df: pd.DataFrame) -> dict:
        """Retorna estatísticas sobre as ocorrências detectadas."""
        if 'UNCOMMANDED_ACT' not in df.columns:
            return {"error": "Execute detect_uncommanded_motion primeiro."}
            
        total_points = len(df)
        unc_points = df['UNCOMMANDED_ACT'].sum()
        
        report = {
            "total_records": total_points,
            "uncommanded_count": int(unc_points),
            "uncommanded_ratio": float(unc_points / total_points) if total_points > 0 else 0,
            "max_delta_ail": float(df['DELTA_AIL_T_POS'].max()) if 'DELTA_AIL_T_POS' in df.columns else 0,
            "max_delta_elev": float(df['DELTA_ELEV_T_POS'].max()) if 'DELTA_ELEV_T_POS' in df.columns else 0
        }
        return report

if __name__ == "__main__":
    # Teste rápido se o arquivo consolidado existir
    import os
    csv_path = "data/raw/TRIMM_COMBINED.csv"
    if os.path.exists(csv_path):
        # Lê pulando os metadados (3 linhas) e a linha de unidades (1 linha) = 4 linhas
        data = pd.read_csv(csv_path, skiprows=4, header=None)
        
        # Como pulamos o header, precisamos ler o header separadamente ou defini-lo
        cols = pd.read_csv(csv_path, skiprows=3, nrows=0).columns
        data.columns = cols

        # Garante que colunas de manche são numéricas
        for c in ['Stick_FWD', 'Stick_AFT']:
            if c in data.columns:
                data[c] = pd.to_numeric(data[c], errors='coerce').fillna(0)

        analyzer = TrimmAnalyzer()
        processed = analyzer.detect_uncommanded_motion(data)
        print("Relatório de Atuação Não Comandada:")
        print(analyzer.get_summary_report(processed))
