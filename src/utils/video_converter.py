from __future__ import annotations

import os
import subprocess
import shutil
from pathlib import Path

def get_ffmpeg_path() -> str | None:
    """Busca o ffmpeg no sistema operacional ou na pasta local tools/"""
    # Tenta encontrar instalado nativamente (MacOS/Linux/Windows PATH)
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
        
    # Fallback para caso Windows offline (pasta tools/)
    local_ffmpeg = Path("tools/ffmpeg.exe")
    if local_ffmpeg.exists() and local_ffmpeg.is_file():
        return str(local_ffmpeg.absolute())
        
    return None

def is_ffmpeg_installed() -> bool:
    """Verifica se o ffmpeg foi encontrado."""
    return get_ffmpeg_path() is not None

def convert_video(input_path: str | Path, output_path: str | Path, rotate: bool = False) -> bool:
    """
    Converte um vídeo MPG para MP4.
    Se rotate for True, aplica rotação de 90 graus para a direita.
    Retorna True em caso de sucesso.
    """
    ffmpeg_exec = get_ffmpeg_path()
    if not ffmpeg_exec:
        raise FileNotFoundError("FFmpeg não encontrado. Instale via Homebrew (MacOS) ou coloque em tools/ffmpeg.exe (Windows).")
        
    cmd = [
        ffmpeg_exec,
        "-y", # Sobrescreve sem perguntar
        "-i", str(input_path)
    ]
    
    # Parâmetros de codificação:
    # libx264 é compatível com HTML5.
    # preset 'fast' ou 'veryfast' ajuda a não demorar horas.
    # crf 28 mantém uma qualidade visual aceitável reduzindo o tamanho do arquivo.
    cmd.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-c:a", "aac"])
    
    if rotate:
        # transpose=1 gira 90 graus no sentido horário (Clockwise)
        cmd.extend(["-vf", "transpose=1"])
        
    cmd.append(str(output_path))
    
    try:
        # Executa o processo de conversão
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"Erro FFmpeg:\n{result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Erro ao executar ffmpeg: {e}")
        return False
