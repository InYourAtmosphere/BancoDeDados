"""Download e extração do MovieLens 20M (GroupLens) para data/raw/."""

import argparse
from pathlib import Path

URL = "https://files.grouplens.org/datasets/movielens/ml-20m.zip"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()


if __name__ == "__main__":
    main()
