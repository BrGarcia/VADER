import os
from pathlib import Path
from typing import Dict, List, Optional

BASE_ANALYSIS_DIR = Path("Arquivos_para_analise")

def get_available_flights() -> List[str]:
    """Lista todas as subpastas (voos) dentro do diretório base."""
    if not BASE_ANALYSIS_DIR.exists():
        return []
    
    flights = [p.name for p in BASE_ANALYSIS_DIR.iterdir() if p.is_dir() and not p.name.startswith('.')]
    return sorted(flights)

def scan_flight_folder(folder_name: str) -> Dict[str, object]:
    """
    Entra na pasta do voo e mapeia os caminhos absolutos dos arquivos necessários.
    """
    flight_dir = BASE_ANALYSIS_DIR / folder_name
    result = {
        "vadr_csv_path": None,
        "dtc_files_paths": [],
        "eicas_video_paths": [],
        "chvc_video_paths": [],
        "flight_dir": flight_dir.absolute()
    }
    
    if not flight_dir.exists():
        return result
        
    # Busca CSV VADR (na raiz ou subpasta VADR)
    vadr_dir = flight_dir / "VADR"
    csv_files = list(flight_dir.glob("*.csv"))
    if vadr_dir.exists():
        csv_files.extend(list(vadr_dir.glob("*.csv")))
    
    if csv_files:
        result["vadr_csv_path"] = csv_files[0].absolute()
        
    # Busca DTC (na raiz ou subpasta DTC)
    dtc_dir = flight_dir / "DTC"
    dtc_files = list(flight_dir.glob("TRIMM*.DMP"))
    if dtc_dir.exists():
        dtc_files.extend(list(dtc_dir.glob("TRIMM*.DMP")))
    
    result["dtc_files_paths"] = [f.absolute() for f in sorted(dtc_files)]
    
    # Busca vídeos EICAS e CHVC
    video_exts = ("*.mp4", "*.MP4", "*.avi", "*.AVI", "*.mkv", "*.mov", "*.mpg", "*.MPG", "*.mpeg", "*.MPEG")
    
    eicas_dir = flight_dir / "EICAS"
    if eicas_dir.exists():
        for ext in video_exts:
            vids = list(eicas_dir.glob(ext))
            if vids:
                result["eicas_video_paths"] = [v.absolute() for v in sorted(vids)]
                break
                
    chvc_dir = flight_dir / "CHVC"
    if chvc_dir.exists():
        for ext in video_exts:
            vids = list(chvc_dir.glob(ext))
            if vids:
                result["chvc_video_paths"] = [v.absolute() for v in sorted(vids)]
                break
                
    return result
