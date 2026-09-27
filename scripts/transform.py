"""ETL para desnormalização e geração de JSON Lines."""

import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-ratings", type=int, default=100000)
    args = parser.parse_args()


if __name__ == "__main__":
    main()
