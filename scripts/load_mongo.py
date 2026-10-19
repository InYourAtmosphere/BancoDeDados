#!/usr/bin/env python3
"""
scripts/load_mongo.py
--------------------------------------------------------------------------------
ETL dos dados brutos do MovieLens (data/raw/) direto para o MongoDB.
Modelo documental:
  - movies : documento rico (embedding de gêneros, links, tags e métricas)
  - ratings: coleção referenciada (user_id, movie_id)
Re-executável: derruba as coleções antes de carregar.
--------------------------------------------------------------------------------
"""

import argparse
import os
import sys
import time

import pandas as pd
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import PyMongoError

from common import MONGO_URI, extract_title_and_year


def parse_args():
    p = argparse.ArgumentParser(description="ETL MovieLens -> MongoDB")
    p.add_argument("--raw-dir", default="data/raw")
    p.add_argument("--uri", default=MONGO_URI)
    p.add_argument("--db-name", default="movielens")
    p.add_argument("--batch-size", type=int, default=5000)
    p.add_argument("--sample-ratings", type=int, default=100000,
                   help="Limite de ratings (padrão: 100000). 0 ou --all-ratings carrega os 20M.")
    p.add_argument("--all-ratings", action="store_true")
    return p.parse_args()


def insert_batches(collection, docs, batch_size):
    for i in range(0, len(docs), batch_size):
        collection.insert_many(docs[i : i + batch_size], ordered=False)


def load_ratings(db, raw_dir, batch_size, limit):
    """Insere ratings em chunks e devolve (soma, contagem) por filme para as métricas."""
    total = 0
    sums = pd.Series(dtype="float64")
    counts = pd.Series(dtype="float64")
    for chunk in pd.read_csv(os.path.join(raw_dir, "rating.csv"), chunksize=200_000):
        if limit:
            chunk = chunk.iloc[: limit - total]

        g = chunk.groupby("movieId")["rating"]
        sums = sums.add(g.sum(), fill_value=0)
        counts = counts.add(g.count(), fill_value=0)

        rated_at = pd.to_datetime(chunk["timestamp"], unit="s").dt.to_pydatetime()
        docs = [
            {"_id": f"{u}_{m}", "user_id": u, "movie_id": m, "rating": r, "rated_at": t}
            for u, m, r, t in zip(chunk["userId"].tolist(), chunk["movieId"].tolist(),
                                  chunk["rating"].tolist(), rated_at)
        ]
        insert_batches(db.ratings, docs, batch_size)
        total += len(docs)
        print(f"    - {total:,} ratings...")
        if limit and total >= limit:
            break
    print(f"[+] ratings={total:,}")
    return sums, counts


def load_movies(db, raw_dir, batch_size, sums, counts):
    links_df = pd.read_csv(os.path.join(raw_dir, "link.csv"), dtype={"imdbId": str})
    links = {
        m: {"imdb": i.zfill(7) if pd.notna(i) else None, "tmdb": int(t) if pd.notna(t) else None}
        for m, i, t in zip(links_df["movieId"], links_df["imdbId"], links_df["tmdbId"])
    }

    tags_df = pd.read_csv(os.path.join(raw_dir, "tag.csv")).dropna(subset=["tag"])
    tags_df["tag"] = tags_df["tag"].str.strip().str.lower()
    tags_df = tags_df[tags_df["tag"] != ""]
    tags = tags_df.groupby("movieId")["tag"].agg(lambda s: sorted(set(s))).to_dict()

    docs = []
    for mid, raw_title, raw_genres in pd.read_csv(os.path.join(raw_dir, "movie.csv")).itertuples(index=False):
        title, year = extract_title_and_year(raw_title)
        genres = [g for g in raw_genres.split("|") if g and g != "(no genres listed)"]
        n = int(counts.get(mid, 0))
        docs.append({
            "_id": mid,
            "title": title,
            "release_year": year,
            "genres": genres,
            "links": links.get(mid, {"imdb": None, "tmdb": None}),
            "metrics": {
                "avg_rating": round(sums[mid] / n, 2) if n else None,
                "rating_count": n,
            },
            "tags": tags.get(mid, []),
        })
    insert_batches(db.movies, docs, batch_size)
    print(f"[+] movies={len(docs):,}")


def create_indexes(db):
    db.movies.create_index([("release_year", ASCENDING)], name="idx_release_year")
    db.movies.create_index([("genres", ASCENDING)], name="idx_multikey_genres")
    db.movies.create_index([("tags", ASCENDING)], name="idx_multikey_tags")
    db.movies.create_index([("metrics.avg_rating", DESCENDING)], name="idx_metrics_avg_rating")
    db.ratings.create_index([("movie_id", ASCENDING)], name="idx_ratings_movie_id")
    db.ratings.create_index([("user_id", ASCENDING)], name="idx_ratings_user_id")
    print("[+] índices criados")


def main():
    args = parse_args()
    t0 = time.time()
    limit = 0 if args.all_ratings else args.sample_ratings

    client = MongoClient(args.uri, serverSelectionTimeoutMS=4000)
    try:
        client.admin.command("ping")
    except PyMongoError as e:
        sys.exit(f"[!] Sem conexão com o MongoDB ({e}).\n    Suba com: docker compose up -d mongodb")

    db = client[args.db_name]
    db.movies.drop()
    db.ratings.drop()

    sums, counts = load_ratings(db, args.raw_dir, args.batch_size, limit)
    load_movies(db, args.raw_dir, args.batch_size, sums, counts)
    create_indexes(db)
    print(f"[+] Concluído em {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
