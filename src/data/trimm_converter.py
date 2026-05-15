"""
trimm_converter.py
Consolida arquivos .DMP da pasta TRIMM em um único CSV compatível com o V.A.D.E.R.
"""

import os
import pandas as pd
import numpy as np

def convert_trimm_to_csv(trimm_dir="TRIMM", output_path="data/raw/TRIMM_COMBINED.csv"):
    """
    Lê os arquivos TRIMM001.DMP a TRIMM005.DMP, concatena e salva como CSV.
    Aplica o cabeçalho fornecido pelo usuário (ajustado para as colunas presentes).
    """
    if not os.path.exists(trimm_dir):
        print(f"Erro: Pasta {trimm_dir} não encontrada.")
        return False

    # Lista arquivos .DMP ordenados
    files = sorted([f for f in os.listdir(trimm_dir) if f.endswith(".DMP")])
    if not files:
        print("Aviso: Nenhum arquivo .DMP encontrado.")
        return False

    print(f"Consolidando {len(files)} arquivos: {files}")

    all_data = []
    for f in files:
        path = os.path.join(trimm_dir, f)
        # Lê usando ; como separador. O motor python lida melhor com separadores no final da linha.
        df = pd.read_csv(path, sep=';', header=None, engine='python')
        
        # Remove a última coluna se estiver toda vazia (comum devido ao ; no final da linha)
        if df.iloc[:, -1].isna().all() or (df.iloc[:, -1] == "").all():
            df = df.iloc[:, :-1]
            
        all_data.append(df)

    if not all_data:
        return False

    combined = pd.concat(all_data, ignore_index=True)

    # Mapeamento de colunas baseado no cabeçalho fornecido e na estrutura observada (18 colunas)
    # Cabeçalho original do usuário: UTC;Hora;Emer_ON;Emer_SW;Stick_FWD;Stick_AFT;CAS;TAS;GS;BARO;
    #                               RALT;PITCH_ANG;ROLL_ANG;AIL_T_POS;ELEV_T_POS;RUD_T_POS;
    #                               PITCH_MIS;ROLL_MIS;Yellow_Zone;Aileron_Test;Elevator_Test
    
    # Ajuste: Removendo 'Hora' (não detectado como coluna separada) e as de Teste no fim se excederem 18.
    actual_headers = [
        "UTC", "Emer_ON", "Emer_SW", "Stick_FWD", "Stick_AFT", 
        "CAS", "TAS", "GS", "BARO", "RALT", 
        "PITCH_ANG", "ROLL_ANG", "AIL_T_POS", "ELEV_T_POS", "RUD_T_POS", 
        "PITCH_MIS", "ROLL_MIS", "Yellow_Zone"
    ]

    # Se o arquivo tiver mais colunas, adicionamos os nomes de teste
    if combined.shape[1] >= 19:
        actual_headers.append("Aileron_Test")
    if combined.shape[1] >= 20:
        actual_headers.append("Elevator_Test")
    if combined.shape[1] >= 21:
        actual_headers.append("Hora") # Caso 'Hora' esteja no fim por algum motivo

    # Garante que temos nomes suficientes ou corta
    combined.columns = actual_headers[:combined.shape[1]]

    # Limpeza e Tipagem
    # 1. Converte F/T para 0/1
    for col in ["Emer_ON", "Emer_SW", "Stick_FWD", "Stick_AFT"]:
        if col in combined.columns:
            combined[col] = combined[col].map({'F': 0, 'T': 1, 'f': 0, 't': 1}).fillna(0).astype(int)

    # 2. Converte 'X.X' e outros para numérico
    numeric_cols = ["CAS", "TAS", "GS", "BARO", "RALT", "PITCH_ANG", "ROLL_ANG", 
                    "AIL_T_POS", "ELEV_T_POS", "RUD_T_POS"]
    for col in numeric_cols:
        if col in combined.columns:
            combined[col] = pd.to_numeric(combined[col].astype(str).replace('X.X', np.nan), errors='coerce')

    # 3. Cria coluna TIME (segundos decorridos) a partir do UTC (ms)
    # Se UTC for um timestamp em ms, calculamos o delta.
    combined['UTC'] = pd.to_numeric(combined['UTC'], errors='coerce')
    t_start = combined['UTC'].min()
    combined['TIME'] = (combined['UTC'] - t_start) / 1000.0
    
    # 4. Aliases para compatibilidade com componentes UI do VADER
    # Mapeia nomes do TRIMM para os nomes esperados pelo AttitudeBox e outros
    mapping = {
        "PITCH_ANG": "APA",
        "ROLL_ANG": "ARA",
        "BARO": "BALT",
        "CAS": "AS",
        "RALT": "RAD_ALT"
    }
    for old_col, new_col in mapping.items():
        if old_col in combined.columns:
            combined[new_col] = combined[old_col]

    # Adiciona colunas ausentes como NaN para evitar erros nos componentes
    for missing in ["NZ", "AOA", "MACH", "PALT", "Q", "ITT", "NG", "NP", "FF", "OT", "OP", "PCL", "MWC_DATA"]:
        if missing not in combined.columns:
            combined[missing] = np.nan

    # Adiciona WOW fake (0 = voo) para compatibilidade com o plotter se necessário
    combined['WOW'] = 0 

    # Salva com metadados mínimos para o DataLoader reconhecer
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("AIRCRAFT,TRIMM-CONSOLIDATED\n")
        f.write("DATE,2026-05-15\n")
        f.write("--------------------------------------------------------------------------------\n")
        # Cabeçalho
        f.write(",".join(combined.columns) + "\n")
        # Linha de unidades (dummy para o DataLoader não pular o primeiro registro de dados)
        f.write(",".join(["units"] * len(combined.columns)) + "\n")
        # Dados
        combined.to_csv(f, header=False, index=False)

    print(f"Sucesso! Arquivo gerado: {output_path} ({len(combined)} linhas)")
    return True

if __name__ == "__main__":
    convert_trimm_to_csv()
