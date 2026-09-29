#!/usr/bin/env python3
"""
scripts/transform.py
--------------------------------------------------------------------------------
Transformação dos dados relacionais/CSVs brutos para o Modelo Documental NoSQL.
Gera arquivos JSON Lines (JSONL) otimizados para MongoDB:
  - data/processed/movies.jsonl  (Documentos ricos com Embedding)
  - data/processed/ratings.jsonl (Coleção referenciada de eventos)
--------------------------------------------------------------------------------
"""

import os
import sys
import re
import json
import time
import argparse
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description="Transformação de Dados para o Modelo de Documentos (MongoDB)"
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default="data/raw",
        help="Diretório com os CSVs originais",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Diretório onde os arquivos JSONL processados serão salvos",
    )
    parser.add_argument(
        "--sample-ratings",
        type=int,
        default=100000,
        help="Quantidade de ratings a processar para teste (padrão: 100000). Use 0 para todos.",
    )
    parser.add_argument(
        "--all-ratings",
        action="store_true",
        help="Processar todos os 20M de ratings",
    )
    return parser.parse_args()


def extract_title_and_year(raw_title: str):
    """Extrai título e ano de lançamento."""
    if not isinstance(raw_title, str):
        return str(raw_title), None
    raw_title = raw_title.strip()
    match = re.search(r"^(.*?)\s*\((\d{4})\)\s*$", raw_title)
    if match:
        return match.group(1).strip(), int(match.group(2))
    return raw_title, None


def main():
    args = parse_args()
    start_time = time.time()
    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 70)
    print("TRANSFORMAÇÃO DE DADOS PARA O MODELO DOCUMENTAL (MONGODB)")
    print("=" * 70)

    # 1. Carregar Links
    links_file = os.path.join(args.raw_dir, "link.csv")
    print(f"[*] Processando links de {links_file}...")
    df_links = pd.read_csv(links_file)
    links_by_movie = {}
    for _, row in df_links.iterrows():
        mid = int(row["movieId"])
        imdb = str(int(row["imdbId"])).zfill(7) if pd.notna(row["imdbId"]) else None
        tmdb = int(row["tmdbId"]) if pd.notna(row["tmdbId"]) else None
        links_by_movie[mid] = {"imdb": imdb, "tmdb": tmdb}

    # 2. Carregar e Agregar Tags por Filme (Embedding de termos únicos)
    tags_file = os.path.join(args.raw_dir, "tag.csv")
    print(f"[*] Agregando tags únicas por filme de {tags_file}...")
    df_tags = pd.read_csv(tags_file).dropna(subset=["tag"])
    tags_by_movie = {}
    for _, row in df_tags.iterrows():
        mid = int(row["movieId"])
        t = str(row["tag"]).strip().lower()
        if not t:
            continue
        if mid not in tags_by_movie:
            tags_by_movie[mid] = set()
        tags_by_movie[mid].add(t)

    # 3. Processar Ratings (Cálculo de métricas pré-computadas + Geração de JSON de ratings)
    ratings_file = os.path.join(args.raw_dir, "rating.csv")
    ratings_out_path = os.path.join(args.output_dir, "ratings.jsonl")
    print(f"[*] Processando ratings e computando métricas de {ratings_file}...")

    movie_stats = {}  # {mid: {"sum": x, "count": y}}
    total_ratings_count = 0
    max_ratings = None if args.all_ratings or args.sample_ratings <= 0 else args.sample_ratings

    with open(ratings_out_path, "w", encoding="utf-8") as f_ratings:
        chunksize = 200000
        for chunk in pd.read_csv(ratings_file, chunksize=chunksize):
            if max_ratings is not None:
                rem = max_ratings - total_ratings_count
                if rem <= 0:
                    break
                if len(chunk) > rem:
                    chunk = chunk.iloc[:rem]

            for row in chunk.itertuples(index=False):
                uid = int(row.userId)
                mid = int(row.movieId)
                val = float(row.rating)
                ts = str(row.timestamp)

                # Estatística acumulada
                if mid not in movie_stats:
                    movie_stats[mid] = {"sum": 0.0, "count": 0}
                movie_stats[mid]["sum"] += val
                movie_stats[mid]["count"] += 1

                # Documento de rating referenciado
                rating_doc = {
                    "_id": f"{uid}_{mid}",
                    "user_id": uid,
                    "movie_id": mid,
                    "rating": val,
                    "rated_at": ts,
                }
                f_ratings.write(json.dumps(rating_doc, ensure_ascii=False) + "\n")
                total_ratings_count += 1

            if max_ratings is not None and total_ratings_count >= max_ratings:
                break

    print(f"[+] Exportados {total_ratings_count:,} ratings para {ratings_out_path}")

    # 4. Processar Filmes e Montar Documentos Ricos (Embedding)
    movies_file = os.path.join(args.raw_dir, "movie.csv")
    movies_out_path = os.path.join(args.output_dir, "movies.jsonl")
    print(f"[*] Gerando documentos estruturados de filmes em {movies_out_path}...")
    df_movies = pd.read_csv(movies_file)

    movies_exported = 0
    with open(movies_out_path, "w", encoding="utf-8") as f_movies:
        for _, row in df_movies.iterrows():
            mid = int(row["movieId"])
            title, year = extract_title_and_year(row["title"])

            raw_genres = str(row["genres"]).split("|") if pd.notna(row["genres"]) else []
            genres = [g.strip() for g in raw_genres if g.strip() and g != "(no genres listed)"]

            # Incorporar subdocumento de links
            link_info = links_by_movie.get(mid, {"imdb": None, "tmdb": None})

            # Incorporar tags únicas
            movie_tags = sorted(list(tags_by_movie.get(mid, set())))

            # Incorporar métricas pré-computadas (Pattern: Computed)
            stats = movie_stats.get(mid, {"sum": 0.0, "count": 0})
            avg_rating = round(stats["sum"] / stats["count"], 2) if stats["count"] > 0 else None

            movie_doc = {
                "_id": mid,
                "title": title,
                "release_year": year,
                "genres": genres,
                "links": link_info,
                "metrics": {
                    "avg_rating": avg_rating,
                    "rating_count": stats["count"],
                },
                "tags": movie_tags,
            }
            f_movies.write(json.dumps(movie_doc, ensure_ascii=False) + "\n")
            movies_exported += 1

    print(f"[+] Exportados {movies_exported:,} documentos de filmes para {movies_out_path}")
    elapsed = time.time() - start_time
    print(f"[+] Transformação para NoSQL concluída com sucesso em {elapsed:.2f}s!")


if __name__ == "__main__":
    main()
