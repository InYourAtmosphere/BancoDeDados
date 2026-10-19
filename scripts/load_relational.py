#!/usr/bin/env python3
import argparse
import io
import os
import time

import pandas as pd

from common import connect, extract_title_and_year

TABLES = ["users", "movies", "genres", "movie_genres", "movie_links",
          "tags", "user_movie_tags", "ratings"]


def parse_args():
    p.add_argument("--raw-dir", default="data/raw")
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=5432)
    p.add_argument("--db", default="movielens")
    p.add_argument("--user", default="postgres")
    p.add_argument("--password", default=None)
    p.add_argument("--sample-ratings", type=int, default=100000,
                   help="Limite de ratings (padrão: 100000). 0 ou --all-ratings carrega os 20M.")
    p.add_argument("--all-ratings", action="store_true")
    return p.parse_args()


def copy(cur, table, df):
    """Carrega o DataFrame na tabela (colunas na ordem do df) via COPY."""
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False)
    buf.seek(0)
    cur.copy_expert(f"COPY {table} ({', '.join(df.columns)}) FROM STDIN WITH (FORMAT csv)", buf)


def load_movies_and_genres(cur, raw_dir):
    df = pd.read_csv(os.path.join(raw_dir, "movie.csv"))
    parsed = df["title"].map(extract_title_and_year)
    movies = pd.DataFrame({
        "movie_id": df["movieId"],
        "title": parsed.str[0],
        "release_year": parsed.str[1].astype("Int64"),
    })
    copy(cur, "movies", movies)

    mg = df.assign(name=df["genres"].str.split("|")).explode("name")
    mg["name"] = mg["name"].str.strip()
    mg = mg[mg["name"].notna() & (mg["name"] != "") & (mg["name"] != "(no genres listed)")]

    copy(cur, "genres", mg[["name"]].drop_duplicates())
    cur.execute("SELECT name, genre_id FROM genres")
    gid = dict(cur.fetchall())
    links = pd.DataFrame({"movie_id": mg["movieId"], "genre_id": mg["name"].map(gid)})
    copy(cur, "movie_genres", links.drop_duplicates())
    print(f"[+] movies={len(movies):,} genres={len(gid):,} movie_genres={len(links):,}")


def load_movie_links(cur, raw_dir):
    df = pd.read_csv(os.path.join(raw_dir, "link.csv"), dtype={"imdbId": str})
    links = pd.DataFrame({
        "movie_id": df["movieId"],
        "imdb_id": df["imdbId"].str.zfill(7),
        "tmdb_id": df["tmdbId"].astype("Int64"),
    })
    copy(cur, "movie_links", links)
    print(f"[+] movie_links={len(links):,}")


def load_tags(cur, raw_dir, seen_users):
    df = pd.read_csv(os.path.join(raw_dir, "tag.csv")).dropna(subset=["tag"])
    df["tag"] = df["tag"].str.strip().str.lower()
    df = df[df["tag"] != ""]

    copy(cur, "tags", df[["tag"]].drop_duplicates().rename(columns={"tag": "tag_name"}))
    cur.execute("SELECT tag_name, tag_id FROM tags")
    tid = dict(cur.fetchall())

    copy(cur, "users", pd.DataFrame({"user_id": sorted(df["userId"].unique())}))
    seen_users.update(df["userId"].unique())

    umt = pd.DataFrame({
        "user_id": df["userId"],
        "movie_id": df["movieId"],
        "tag_id": df["tag"].map(tid),
        "tagged_at": pd.to_datetime(df["timestamp"], unit="s"),
    }).drop_duplicates()  # PK (user, movie, tag, tagged_at)
    copy(cur, "user_movie_tags", umt)
    print(f"[+] tags={len(tid):,} user_movie_tags={len(umt):,}")


def load_ratings(cur, raw_dir, seen_users, limit):
    total = 0
    for chunk in pd.read_csv(os.path.join(raw_dir, "rating.csv"), chunksize=500_000):
        if limit:
            chunk = chunk.iloc[: limit - total]
        new = set(chunk["userId"].unique()) - seen_users
        copy(cur, "users", pd.DataFrame({"user_id": sorted(new)}))
        seen_users.update(new)

        copy(cur, "ratings", pd.DataFrame({
            "user_id": chunk["userId"],
            "movie_id": chunk["movieId"],
            "rating": chunk["rating"],
            "rated_at": pd.to_datetime(chunk["timestamp"], unit="s"),
        }))
        total += len(chunk)
        print(f"    - {total:,} ratings...")
        if limit and total >= limit:
            break
    print(f"[+] ratings={total:,} users={len(seen_users):,}")


def main():
    args = parse_args()
    t0 = time.time()
    limit = 0 if args.all_ratings else args.sample_ratings

    conn = connect(args.host, args.port, args.db, args.user, args.password)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE")
            seen_users = set()
            load_movies_and_genres(cur, args.raw_dir)
            load_movie_links(cur, args.raw_dir)
            load_tags(cur, args.raw_dir, seen_users)
            load_ratings(cur, args.raw_dir, seen_users, limit)
        with conn.cursor() as cur:
            cur.execute("ANALYZE")
            conn.commit()
    finally:
        conn.close()
    print(f"[+] Concluído em {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
