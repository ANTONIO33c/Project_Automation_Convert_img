"""
Seleciona automaticamente a melhor foto de cada produto quando há várias
fotos do mesmo item em ângulos diferentes.

Estratégia:
  1. Identifica quais fotos são do MESMO produto usando reconhecimento de
     características do objeto (ORB feature matching) confirmado por
     verificação geométrica (RANSAC/homografia) - o mesmo princípio usado
     em reconhecimento visual de objetos. Ele acha pontos-chave
     característicos (cantos, texturas, bordas) em cada imagem e verifica
     se esses pontos se encaixam numa transformação geométrica consistente
     entre duas fotos (rotação/perspectiva) - isso é o que realmente
     acontece quando é o mesmo objeto visto de outro ângulo, e evita os
     falsos positivos que uma simples contagem de pontos parecidos geraria.
     Funciona mesmo com ângulo, distância ou iluminação diferentes -
     ao contrário de um hash de imagem, que só reconhece fotos quase
     idênticas.
  2. Dentro de cada grupo (mesmo produto), escolhe a foto mais nítida
     usando a variância do Laplaciano (métrica padrão de detecção de
     foco/blur).
  3. Copia a foto vencedora de cada grupo para "escolhidas/" e as demais
     do grupo para "descartadas/" (ou apaga de vez, se pedido).

Uso:
    python selecionar_melhor_foto.py --input ./fotos --output ./resultado

    Isso cria dentro de --output:
        resultado/escolhidas/    -> a melhor foto de cada produto
        resultado/descartadas/   -> as demais fotos do mesmo produto (perderam)

Dependências:
    pip install opencv-python-headless numpy pillow
"""

import argparse
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFilter


IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

# Kernel 3x3 clássico de Laplaciano, pra medir nitidez sem depender do OpenCV
_LAPLACIAN_KERNEL = ImageFilter.Kernel(
    size=(3, 3),
    kernel=[0, 1, 0,
            1, -4, 1,
            0, 1, 0],
    scale=1,
    offset=0,
)


def sharpness_score(path: Path) -> float:
    """Variância do Laplaciano: quanto maior, mais nítida a imagem."""
    try:
        with Image.open(path) as img:
            cinza = img.convert("L")
            filtrada = cinza.filter(_LAPLACIAN_KERNEL)
            arr = np.asarray(filtrada, dtype=np.float64)
            return float(arr.var())
    except Exception:
        return -1.0


def extrair_descritores(path: Path, orb, max_dimensao: int = 800):
    """Extrai pontos-chave (ORB) de uma imagem, redimensionando se for muito grande
    (deixa o processamento mais rápido sem perder qualidade de reconhecimento)."""
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None, None
    h, w = img.shape
    if max(h, w) > max_dimensao:
        escala = max_dimensao / max(h, w)
        img = cv2.resize(img, (int(w * escala), int(h * escala)))
    kp, des = orb.detectAndCompute(img, None)
    return kp, des


class UnionFind:
    """Estrutura pra agrupar itens conectados (ex: A bate com B, B bate com C
    => A, B e C ficam no mesmo grupo, mesmo que A e C nunca tenham sido comparados)."""

    def __init__(self, itens):
        self.pai = {item: item for item in itens}

    def find(self, item):
        while self.pai[item] != item:
            self.pai[item] = self.pai[self.pai[item]]
            item = self.pai[item]
        return item

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.pai[ra] = rb


def eh_mesmo_produto(kp1, des1, kp2, des2, bf, min_inliers: int) -> bool:
    """Compara duas imagens e decide se mostram o mesmo objeto físico.

    Usa ORB + teste de razão (Lowe) para achar candidatos a match, e depois
    confirma com RANSAC/homografia: só conta como 'mesmo produto' se os
    pontos em comum se encaixarem numa transformação geométrica consistente
    (rotação/perspectiva). Isso é bem mais confiável do que só contar
    quantos pontos parecem semelhantes, que gera falsos positivos entre
    produtos diferentes."""
    if des1 is None or des2 is None or len(des1) < 4 or len(des2) < 4:
        return False

    matches = bf.knnMatch(des1, des2, k=2)
    bons = [m for par in matches if len(par) == 2 for m, n in [par] if m.distance < 0.75 * n.distance]
    if len(bons) < 8:  # mínimo de pontos pra sequer tentar calcular uma homografia
        return False

    src_pts = np.float32([kp1[m.queryIdx].pt for m in bons]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in bons]).reshape(-1, 1, 2)
    _, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    if mask is None:
        return False

    inliers = int(mask.sum())
    return inliers >= min_inliers


def group_by_object_matching(files, min_inliers: int):
    """Agrupa as fotos que mostram o mesmo produto físico, comparando
    características visuais entre TODOS os pares de imagens."""
    orb = cv2.ORB_create(nfeatures=800)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)

    print("Analisando características de cada imagem...")
    keypoints = {}
    descritores = {}
    for f in files:
        kp, des = extrair_descritores(f, orb)
        keypoints[f] = kp
        descritores[f] = des

    uf = UnionFind(files)

    print("Comparando imagens entre si...")
    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            f1, f2 = files[i], files[j]
            if uf.find(f1) == uf.find(f2):
                continue  # já estão no mesmo grupo, não precisa comparar de novo
            if eh_mesmo_produto(keypoints[f1], descritores[f1], keypoints[f2], descritores[f2], bf, min_inliers):
                uf.union(f1, f2)

    grupos_dict = {}
    for f in files:
        raiz = uf.find(f)
        grupos_dict.setdefault(raiz, []).append(f)

    return list(grupos_dict.values())


def main():
    ap = argparse.ArgumentParser(description="Seleciona a melhor foto de cada produto.")
    ap.add_argument("--input", required=True, help="Pasta com todas as fotos")
    ap.add_argument("--output", required=True, help="Pasta onde salvar as melhores fotos")
    ap.add_argument("--min-inliers", type=int, default=55,
                     help="Nº mínimo de pontos confirmados geometricamente (RANSAC) para "
                          "considerar duas fotos como sendo do mesmo produto (padrão: 25). "
                          "Aumente se estiver juntando produtos diferentes; diminua se estiver "
                          "separando fotos que deveriam ficar juntas.")
    ap.add_argument("--deletar-descartadas", action="store_true",
                     help="Apaga de vez (irreversível) as fotos perdedoras da pasta de origem. "
                          "Sem essa flag, elas só são copiadas para output/descartadas/.")
    ap.add_argument("--forcar", action="store_true",
                     help="Pula a confirmação interativa ao usar --deletar-descartadas")
    args = ap.parse_args()

    if args.deletar_descartadas and not args.forcar:
        print("ATENÇÃO: --deletar-descartadas vai apagar de vez os arquivos perdedores")
        print("da pasta de origem. Essa ação NÃO pode ser desfeita.")
        resposta = input("Digite 'apagar' para confirmar e continuar: ").strip().lower()
        if resposta != "apagar":
            print("Operação cancelada. Nenhum arquivo foi apagado.")
            return

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    escolhidas_dir = output_dir / "escolhidas"
    escolhidas_dir.mkdir(parents=True, exist_ok=True)

    if not args.deletar_descartadas:
        descartadas_dir = output_dir / "descartadas"
        descartadas_dir.mkdir(parents=True, exist_ok=True)

    arquivos = [p for p in sorted(input_dir.iterdir()) if p.suffix.lower() in IMG_EXTS]
    if not arquivos:
        print("Nenhuma imagem encontrada na pasta de entrada.")
        return

    print(f"Total de imagens: {len(arquivos)}\n")

    todos_grupos = group_by_object_matching(arquivos, args.min_inliers)

    print(f"\nGrupos de produtos identificados: {len(todos_grupos)}")

    for i, grupo in enumerate(todos_grupos, start=1):
        pontuados = [(f, sharpness_score(f)) for f in grupo]
        pontuados.sort(key=lambda x: x[1], reverse=True)
        melhor, score = pontuados[0]

        shutil.copy2(melhor, escolhidas_dir / melhor.name)

        print(f"\nGrupo {i} ({len(grupo)} foto(s)):")
        for f, s in pontuados:
            if f == melhor:
                print(f"   {f.name}  (nitidez={s:.1f}) <-- escolhida")
            elif args.deletar_descartadas:
                f.unlink()
                print(f"   {f.name}  (nitidez={s:.1f})  -> apagada da origem")
            else:
                shutil.copy2(f, descartadas_dir / f.name)
                print(f"   {f.name}  (nitidez={s:.1f})  -> descartada")

    total_descartadas = sum(len(g) for g in todos_grupos) - len(todos_grupos)
    print(f"\nPronto!")
    print(f"  {len(todos_grupos)} imagens escolhidas em: {escolhidas_dir}")
    if args.deletar_descartadas:
        print(f"  {total_descartadas} imagens apagadas de vez da pasta de origem")
    else:
        print(f"  {total_descartadas} imagens descartadas em: {descartadas_dir}")


if __name__ == "__main__":
    main()