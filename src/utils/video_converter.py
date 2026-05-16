import os
import subprocess
from pathlib import Path

FFMPEG_PATH = Path("tools/ffmpeg.exe")

def is_ffmpeg_installed() -> bool:
    """Verifica se o ffmpeg.exe está na pasta tools/"""
    return FFMPEG_PATH.exists() and FFMPEG_PATH.is_file()

def convert_video(input_path: str | Path, output_path: str | Path, rotate: bool = False) -> bool:
    """
    Converte um vídeo MPG para MP4.
    Se rotate for True, aplica rotação de 90 graus para a direita.
    Retorna True em caso de sucesso.
    """
    if not is_ffmpeg_installed():
        raise FileNotFoundError("ffmpeg.exe não encontrado na pasta tools/. Por favor, baixe e coloque o executável lá.")
        
    cmd = [
        str(FFMPEG_PATH.absolute()),
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
