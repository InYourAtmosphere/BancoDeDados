"""Download e extração do MovieLens 20M (GroupLens) para data/raw/.

Baixa o pacote oficial ml-20m.zip, extrai os CSVs e os renomeia para os
nomes no singular que os scripts de ETL (load_relational.py / transform.py)
esperam encontrar em data/raw/.
"""

import argparse
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

URL = "https://files.grouplens.org/datasets/movielens/ml-20m.zip"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Mapeia os nomes do dataset (plural) -> nomes esperados pelos scripts (singular)
FILE_MAP = {
    "movies.csv": "movie.csv",
    "ratings.csv": "rating.csv",
    "tags.csv": "tag.csv",
    "links.csv": "link.csv",
    "genome-scores.csv": "genome-scores.csv",
    "genome-tags.csv": "genome-tags.csv",
}


def _progress(block_num, block_size, total_size):
    if total_size <= 0:
        return
    downloaded = block_num * block_size
    pct = min(downloaded / total_size * 100, 100)
    mb = downloaded / (1024 * 1024)
    total_mb = total_size / (1024 * 1024)
    sys.stdout.write(f"\r  Baixando: {pct:5.1f}%  ({mb:6.1f} / {total_mb:6.1f} MB)")
    sys.stdout.flush()


def already_present() -> bool:
    """Retorna True se os 4 CSVs essenciais já existem em data/raw/."""
    essentials = ["movie.csv", "rating.csv", "tag.csv", "link.csv"]
    return all((RAW_DIR / name).exists() for name in essentials)


def main():
    parser = argparse.ArgumentParser(
        description="Baixa e extrai o MovieLens 20M para data/raw/."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Baixa novamente mesmo que os CSVs já existam em data/raw/.",
    )
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if already_present() and not args.force:
        print("CSVs já presentes em data/raw/. Use --force para baixar de novo.")
        return

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        zip_path = tmp_dir / "ml-20m.zip"

        print(f"Origem : {URL}")
        print(f"Destino: {RAW_DIR}")
        try:
            urllib.request.urlretrieve(URL, zip_path, reporthook=_progress)
        except Exception as exc:  # noqa: BLE001
            sys.exit(f"\n[ERRO] Falha no download: {exc}")
        print("\n  Download concluído. Extraindo CSVs...")

        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                src_name = Path(member).name
                if src_name not in FILE_MAP:
                    continue
                dest = RAW_DIR / FILE_MAP[src_name]
                with zf.open(member) as src, open(dest, "wb") as out:
                    out.write(src.read())
                print(f"    -> {dest.name}")

    print("Pronto. Dados brutos disponíveis em data/raw/.")


if __name__ == "__main__":
    main()
