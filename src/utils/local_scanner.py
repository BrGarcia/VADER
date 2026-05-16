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
    
    def _filter_best_videos(video_list: list[Path]) -> list[Path]:
        """Agrupa os vídeos pelo nome. Se houver .mp4 e .mpg do mesmo vídeo, retorna apenas o .mp4."""
        basenames = {}
        for v in video_list:
            base = v.stem
            if base not in basenames:
                basenames[base] = []
            basenames[base].append(v)
            
        best_paths = []
        for base, paths in basenames.items():
            mp4_path = next((p for p in paths if p.suffix.lower() == ".mp4"), None)
            if mp4_path:
                best_paths.append(mp4_path)
            else:
                best_paths.append(paths[0])
        return sorted(best_paths)

    # Busca vídeos EICAS e CHVC
    video_exts = ("*.mp4", "*.MP4", "*.avi", "*.AVI", "*.mkv", "*.mov", "*.mpg", "*.MPG", "*.mpeg", "*.MPEG")
    
    eicas_dir = flight_dir / "EICAS"
    if eicas_dir.exists():
        vids = []
        for ext in video_exts:
            vids.extend(list(eicas_dir.glob(ext)))
        if vids:
            result["eicas_video_paths"] = _filter_best_videos([v.absolute() for v in vids])
                
    chvc_dir = flight_dir / "CHVC"
    if chvc_dir.exists():
        vids = []
        for ext in video_exts:
            vids.extend(list(chvc_dir.glob(ext)))
        if vids:
            result["chvc_video_paths"] = _filter_best_videos([v.absolute() for v in vids])
                
    return result
