"""ETL para normalização 3FN e carga no banco relacional (SQLite)."""

import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-ratings", type=int, default=100000)
    parser.add_argument("--all-ratings", action="store_true")
    args = parser.parse_args()


if __name__ == "__main__":
    main()
