
"""
Conversor/Compactador de imagens
--------------------------------
Converte imagens (JPG, PNG, HEIC) para WEBP e/ou compacta a qualidade delas.

Instalação das dependências (rodar uma vez no terminal do VSCode):
    pip install Pillow pillow-heif

Exemplos de uso:

  1) Só converter para webp (sem perder qualidade):
     python converter_imagens.py --entrada ./entrada --saida ./saida --modo converter

  2) Só compactar (mantendo o formato original, reduzindo a qualidade em 30%):
     python conversor_img.py --entrada ./entrada --saida ./saida --modo compactar

  3) Converter para webp E compactar ao mesmo tempo:
     python converter_imagens.py --entrada ./entrada --saida ./saida --modo ambos

  Você pode ajustar o quanto quer reduzir a qualidade com --qualidade (padrão: 70,
  ou seja, reduz 30% da qualidade original).


  Questões de Exclusão do arquivo da pasta de Entrada

  ao gerar o promp para realizar os processo caso queira manter os arquivo originais nas pasta de entrada 
  é só adicionar: --manter-original ao final do comando

  Caso não adicione nada ele irá validar o arquivo na pasta de Saída e logo após excluir o arquivo da pasta de Entrada.
"""

import argparse
import sys
from pathlib import Path

from PIL import Image

# Habilita suporte a HEIC/HEIF no Pillow
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    print("Aviso: 'pillow-heif' não está instalado. Arquivos .heic/.heif serão ignorados.")
    print("Instale com: pip install pillow-heif\n")

EXTENSOES_SUPORTADAS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"}


def processar_imagem(caminho_entrada: Path, pasta_saida: Path, modo: str, qualidade: int, apagar_original: bool):
    """Processa uma única imagem de acordo com o modo escolhido."""
    try:
        imagem = Image.open(caminho_entrada)

        # Remove canal alpha se for converter para formatos que não suportam (ex: jpg)
        if imagem.mode in ("RGBA", "P") and modo == "compactar" and caminho_entrada.suffix.lower() in (".jpg", ".jpeg"):
            imagem = imagem.convert("RGB")

        if modo == "converter":
            # Só converte o formato para webp, mantém qualidade alta (sem compactar)
            destino = pasta_saida / (caminho_entrada.stem + ".webp")
            imagem.save(destino, "WEBP", quality=95)

        elif modo == "compactar":
            # Mantém o formato original, mas reduz a qualidade
            destino = pasta_saida / caminho_entrada.name
            formato = imagem.format if imagem.format else "JPEG"
            if formato.upper() == "PNG":
                # PNG usa 'compress_level' (0-9) em vez de 'quality'
                imagem.save(destino, "PNG", optimize=True, compress_level=8)
            else:
                imagem.save(destino, formato, quality=qualidade, optimize=True)

        elif modo == "ambos":
            # Converte para webp E aplica a qualidade reduzida
            destino = pasta_saida / (caminho_entrada.stem + ".webp")
            imagem.save(destino, "WEBP", quality=qualidade)

        print(f"OK: {caminho_entrada.name} -> {destino.name}")

        # Só apaga o original depois de confirmar que o arquivo de saída
        # existe de verdade e não está vazio/corrompido
        if apagar_original:
            if destino.exists() and destino.stat().st_size > 0:
                caminho_entrada.unlink()
                print(f"   Original removido da entrada: {caminho_entrada.name}")
            else:
                print(f"   Aviso: arquivo de saída não foi validado, original mantido: {caminho_entrada.name}")

    except Exception as e:
        print(f"Erro ao processar {caminho_entrada.name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Converte e/ou compacta imagens (jpg, png, heic).")
    parser.add_argument("--entrada", required=True, help="Pasta onde estão as imagens originais")
    parser.add_argument("--saida", required=True, help="Pasta onde as imagens processadas serão salvas")
    parser.add_argument(
        "--modo",
        required=True,
        choices=["converter", "compactar", "ambos"],
        help="'converter' = só muda para webp | 'compactar' = só reduz qualidade | 'ambos' = converte e compacta",
    )
    parser.add_argument(
        "--qualidade",
        type=int,
        default=70,
        help="Qualidade final da imagem (0-100). Padrão 70 = reduz 30%% da qualidade.",
    )
    parser.add_argument(
        "--manter-original",
        action="store_true",
        help="Se usado, NÃO apaga o arquivo original da pasta de entrada (padrão é apagar após validar a saída).",
    )

    args = parser.parse_args()

    pasta_entrada = Path(args.entrada).resolve()
    pasta_saida = Path(args.saida).resolve()

    if not pasta_entrada.is_dir():
        print(f"Pasta de entrada não encontrada: {pasta_entrada}")
        sys.exit(1)

    # Cria a pasta de saída uma única vez, antes de processar qualquer imagem
    pasta_saida.mkdir(parents=True, exist_ok=True)
    print(f"Pasta de entrada: {pasta_entrada}")
    print(f"Pasta de saída:   {pasta_saida}\n")

    arquivos = [
        f for f in pasta_entrada.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSOES_SUPORTADAS
    ]

    if not arquivos:
        print("Nenhuma imagem compatível encontrada na pasta de entrada.")
        sys.exit(0)

    apagar_original = not args.manter_original

    print(f"Encontradas {len(arquivos)} imagem(ns). Modo: {args.modo}. Qualidade: {args.qualidade}")
    if apagar_original:
        print("Os originais serão APAGADOS da pasta de entrada após validar a saída.\n")
    else:
        print("Os originais serão MANTIDOS na pasta de entrada (--manter-original ativo).\n")

    for arquivo in arquivos:
        processar_imagem(arquivo, pasta_saida, args.modo, args.qualidade, apagar_original)

    print("\nProcesso concluído!")


if __name__ == "__main__":
    main()