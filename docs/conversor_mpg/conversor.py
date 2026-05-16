import os
import subprocess
from pathlib import Path
import sys
import platform
import shutil

def get_ffmpeg_path():
    """Identifica o OS, procura ou instala o ffmpeg, e retorna o comando para usá-lo."""
    sistema = platform.system()
    base_dir = Path(__file__).parent.absolute()

    if sistema == "Windows":
        # No Windows, priorizamos o ffmpeg.exe na mesma pasta
        ffmpeg_local = base_dir / "ffmpeg.exe"
        if ffmpeg_local.exists():
            return str(ffmpeg_local)
        
        # Tenta ver se está no PATH global do Windows
        ffmpeg_global = shutil.which("ffmpeg")
        if ffmpeg_global:
            return ffmpeg_global
            
        print(f"\n[ERRO] ffmpeg.exe não encontrado no Windows.")
        print(f"Por favor, baixe e cole o ffmpeg.exe na pasta:\n{base_dir}")
        return None

    elif sistema == "Darwin": # MacOS
        # Primeiro, vê se já existe no sistema (via brew ou outro)
        ffmpeg_global = shutil.which("ffmpeg")
        if ffmpeg_global:
            return ffmpeg_global
            
        print("\n[AVISO] FFmpeg não encontrado no MacOS. Tentando instalar via Homebrew...")
        
        # Verifica se tem Homebrew instalado
        if not shutil.which("brew"):
            print("[ERRO] Homebrew não encontrado. Não é possível instalar o FFmpeg automaticamente.")
            print("Instale o Homebrew executando no terminal do Mac:")
            print('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
            return None
            
        # Tenta instalar o ffmpeg usando brew
        try:
            subprocess.run(["brew", "install", "ffmpeg"], check=True)
            print("✅ FFmpeg instalado com sucesso no Mac!")
            return shutil.which("ffmpeg")
        except subprocess.CalledProcessError:
            print("[ERRO] Falha ao tentar instalar o FFmpeg via Homebrew.")
            return None

    elif sistema == "Linux":
        # No linux, apenas checamos o path
        ffmpeg_global = shutil.which("ffmpeg")
        if ffmpeg_global:
            return ffmpeg_global
            
        print("\n[AVISO] FFmpeg não encontrado no Linux.")
        print("Instale usando seu gerenciador de pacotes (ex: sudo apt install ffmpeg).")
        return None

    else:
        print(f"\n[ERRO] Sistema operacional não reconhecido: {sistema}")
        return None


def main():
    print("="*50)
    print("   CONVERSOR E UNIFICADOR DE VÍDEOS MPG -> MP4")
    print("="*50)

    # Identifica a plataforma e obtém o executável do ffmpeg
    ffmpeg_cmd = get_ffmpeg_path()
    if not ffmpeg_cmd:
        input("\nPressione ENTER para sair...")
        return

    base_dir = Path(__file__).parent.absolute()

    # Buscar arquivos .mpg
    mpg_files = list(base_dir.glob("*.mpg"))
    if not mpg_files:
        mpg_files = list(base_dir.glob("*.mpeg"))
        
    # Remove qualquer lixo de processos anteriores
    mpg_files = [f for f in mpg_files if f.name != "unido_temp.mpg"]

    if not mpg_files:
        print(f"\n[AVISO] Nenhum arquivo .mpg ou .mpeg encontrado na pasta:\n{base_dir}")
        input("\nPressione ENTER para sair...")
        return

    # Ordenar alfabeticamente para garantir a sequência
    mpg_files.sort(key=lambda x: x.name)
    
    print(f"\nForam encontrados {len(mpg_files)} arquivos MPG:")
    for f in mpg_files:
        print(f" - {f.name}")
        
    print("\nOpções de processamento:")
    print("1. Converter normalmente (Ideal para HUD)")
    print("2. Converter e rotacionar 90º à direita (Ideal para EICAS)")
    
    opcao = input("\nEscolha uma opção [1/2]: ").strip()
    rotacionar = (opcao == "2")

    nome_saida = input("\nDigite o nome desejado para o arquivo final (sem o .mp4) [Padrão: video_final]: ").strip()
    if not nome_saida:
        nome_saida = "video_final"

    concat_list_path = base_dir / "concat_list.txt"
    output_mpg = base_dir / "unido_temp.mpg"
    output_mp4 = base_dir / f"{nome_saida}.mp4"
    
    if output_mpg.exists(): output_mpg.unlink()
    if output_mp4.exists(): output_mp4.unlink()

    with open(concat_list_path, "w", encoding="utf-8") as f:
        for mpg in mpg_files:
            f.write(f"file '{mpg.name}'\n")

    # ---------------------------------------------------------
    # PASSO 1: UNIR OS MPG
    # ---------------------------------------------------------
    print("\n[Passo 1/2] Unindo arquivos MPG de forma rápida (sem recodificar)...")
    cmd_concat = [
        ffmpeg_cmd,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_path),
        "-c", "copy",
        str(output_mpg)
    ]
    
    res_concat = subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    
    if res_concat.returncode != 0 or not output_mpg.exists():
        print("\n[ERRO] Falha ao unir arquivos MPG.")
        return
        
    print(f" ✅ Arquivos unidos com sucesso!")

    # ---------------------------------------------------------
    # PASSO 2: CONVERTER PARA MP4
    # ---------------------------------------------------------
    print(f"\n[Passo 2/2] Convertendo para {output_mp4.name} (Isso pode demorar)...")
    cmd_convert = [
        ffmpeg_cmd,
        "-y",
        "-i", str(output_mpg),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "28",
        "-c:a", "aac"
    ]
    
    if rotacionar:
        print(" ↪ Aplicando rotação de 90º...")
        cmd_convert.extend(["-vf", "transpose=1"])
        
    cmd_convert.append(str(output_mp4))
    
    res_convert = subprocess.run(cmd_convert)
    
    if res_convert.returncode == 0 and output_mp4.exists():
        print(f"\n🎉 SUCESSO! Arquivo salvo em:\n{output_mp4.absolute()}")
        try:
            concat_list_path.unlink()
            output_mpg.unlink()
            print(" 🧹 Limpeza de arquivos temporários concluída.")
        except:
            pass
    else:
        print("\n[ERRO] Falha durante a conversão final para MP4.")

    input("\nPressione ENTER para sair...")

if __name__ == "__main__":
    main()
