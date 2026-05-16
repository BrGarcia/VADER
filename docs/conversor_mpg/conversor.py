import os
import subprocess
from pathlib import Path
import sys

def main():
    print("="*50)
    print("   CONVERSOR E UNIFICADOR DE VÍDEOS MPG -> MP4")
    print("="*50)

    # Pasta atual do script
    base_dir = Path(__file__).parent.absolute()
    
    # Caminho do ffmpeg
    ffmpeg_path = base_dir / "ffmpeg.exe"
    
    if not ffmpeg_path.exists():
        print(f"\n[ERRO] ffmpeg.exe não encontrado na pasta:\n{base_dir}")
        print("Por favor, cole o ffmpeg.exe na mesma pasta deste script e tente novamente.")
        input("\nPressione ENTER para sair...")
        return

    # Buscar arquivos .mpg
    mpg_files = list(base_dir.glob("*.mpg"))
    if not mpg_files:
        mpg_files = list(base_dir.glob("*.mpeg"))
        
    # Remove qualquer 'unido_temp.mpg' anterior da lista para não tentar unir consigo mesmo
    mpg_files = [f for f in mpg_files if f.name != "unido_temp.mpg"]

    if not mpg_files:
        print(f"\n[AVISO] Nenhum arquivo .mpg ou .mpeg encontrado na pasta:\n{base_dir}")
        input("\nPressione ENTER para sair...")
        return

    # Ordenar alfabeticamente para garantir a sequência correta
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

    # Arquivos de trabalho
    concat_list_path = base_dir / "concat_list.txt"
    output_mpg = base_dir / "unido_temp.mpg"
    output_mp4 = base_dir / f"{nome_saida}.mp4"
    
    # Limpa tentativas anteriores
    if output_mpg.exists():
        output_mpg.unlink()
    if output_mp4.exists():
        output_mp4.unlink()

    # Cria a lista de arquivos para o FFmpeg (Concat Demuxer)
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for mpg in mpg_files:
            # Caminho relativo é mais seguro para o FFmpeg no Windows
            f.write(f"file '{mpg.name}'\n")

    # ---------------------------------------------------------
    # PASSO 1: UNIR OS MPG
    # ---------------------------------------------------------
    print("\n[Passo 1/2] Unindo arquivos MPG de forma rápida (sem recodificar)...")
    cmd_concat = [
        str(ffmpeg_path),
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
        str(ffmpeg_path),
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
    
    # Oculta stdout mas deixa stderr para o FFmpeg mostrar o progresso caso queiramos,
    # porém para manter limpo, vamos jogar stdout para o console normal.
    res_convert = subprocess.run(cmd_convert)
    
    if res_convert.returncode == 0 and output_mp4.exists():
        print(f"\n🎉 SUCESSO! Arquivo salvo em:\n{output_mp4.absolute()}")
        
        # Limpeza dos arquivos temporários
        try:
            concat_list_path.unlink()
            output_mpg.unlink()
            print(" 🧹 Limpeza de arquivos temporários concluída.")
        except Exception as e:
            print(f" [Aviso] Não foi possível apagar os arquivos temporários: {e}")
            
    else:
        print("\n[ERRO] Falha durante a conversão final para MP4.")

    input("\nPressione ENTER para sair...")

if __name__ == "__main__":
    main()
