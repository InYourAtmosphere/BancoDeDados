#!/usr/bin/env python3
"""
scripts/load_relational.py
--------------------------------------------------------------------------------
Script ETL para processar os dados brutos do MovieLens (data/raw/),
aplicar as transformações da 1ª, 2ª e 3ª Formas Normais (3FN),
e carregar os dados no banco relacional (SQLite por padrão, ou PostgreSQL).
--------------------------------------------------------------------------------
"""

import os
import sys
import re
import time
import argparse
import sqlite3
import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description="ETL e Carga do Dataset MovieLens no SGBD Relacional (3FN)"
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default="data/raw",
        help="Diretório onde estão os arquivos CSV brutos (padrão: data/raw)",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="relational/movielens.db",
        help="Caminho do arquivo de banco SQLite de destino (padrão: relational/movielens.db)",
    )
    parser.add_argument(
        "--schema-file",
        type=str,
        default="relational/schema.sql",
        help="Caminho do arquivo schema.sql com DDL (padrão: relational/schema.sql)",
    )
    parser.add_argument(
        "--sample-ratings",
        type=int,
        default=100000,
        help="Quantidade limite de ratings a carregar para teste rápido (padrão: 100000). Use 0 ou --all-ratings para carregar todos os 20M.",
    )
    parser.add_argument(
        "--all-ratings",
        action="store_true",
        help="Carregar todas as 20 milhões de avaliações (pode demorar alguns minutos)",
    )
    return parser.parse_args()


def extract_title_and_year(raw_title: str):
    """
    1FN: Decompõe o título composto em título limpo e ano de lançamento.
    Ex: 'Toy Story (1995)' -> ('Toy Story', 1995)
    """
    if not isinstance(raw_title, str):
        return str(raw_title), None
    raw_title = raw_title.strip()
    match = re.search(r"^(.*?)\s*\((\d{4})\)\s*$", raw_title)
    if match:
        clean_title = match.group(1).strip()
        year = int(match.group(2))
        return clean_title, year
    return raw_title, None


def init_database(db_path: str, schema_file: str) -> sqlite3.Connection:
    """Cria a conexão SQLite e executa o schema.sql."""
    # Garante que o diretório pai exista
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    # Se o banco já existia, remove para carga limpa e determinística
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"[*] Banco anterior removido: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Otimizações de escrita em lote para SQLite
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.execute("PRAGMA foreign_keys = ON;")

    print(f"[*] Executando DDL a partir de: {schema_file}")
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    conn.commit()
    print("[+] Tabelas e índices criados com sucesso.")
    return conn


def load_movies_and_genres(conn: sqlite3.Connection, raw_dir: str):
    """
    Processa movie.csv:
    - Atomiza o título e ano
    - Atomiza a coluna multivalorada genres (1FN) em 'genres' e 'movie_genres'
    """
    csv_path = os.path.join(raw_dir, "movie.csv")
    print(f"\n[*] Lendo e normalizando {csv_path}...")
    df = pd.read_csv(csv_path)

    movies_data = []
    movie_genres_data = []
    genre_to_id = {}
    genre_id_counter = 1

    for _, row in df.iterrows():
        movie_id = int(row["movieId"])
        clean_title, year = extract_title_and_year(row["title"])
        movies_data.append((movie_id, clean_title, year))

        raw_genres = str(row["genres"]).split("|") if pd.notna(row["genres"]) else []
        for g in raw_genres:
            g = g.strip()
            if not g:
                continue
            if g not in genre_to_id:
                genre_to_id[g] = genre_id_counter
                genre_id_counter += 1
            movie_genres_data.append((movie_id, genre_to_id[g]))

    cursor = conn.cursor()

    # 1. Inserir Filmes
    cursor.executemany(
        "INSERT INTO movies (movie_id, title, release_year) VALUES (?, ?, ?);",
        movies_data,
    )
    print(f"[+] Inseridos {len(movies_data):,} filmes em 'movies'.")

    # 2. Inserir Catálogo de Gêneros
    genres_records = [(gid, name) for name, gid in sorted(genre_to_id.items(), key=lambda x: x[1])]
    cursor.executemany(
        "INSERT INTO genres (genre_id, name) VALUES (?, ?);",
        genres_records,
    )
    print(f"[+] Inseridos {len(genres_records):,} gêneros únicos em 'genres'.")

    # 3. Inserir Tabela Associativa N:M
    cursor.executemany(
        "INSERT INTO movie_genres (movie_id, genre_id) VALUES (?, ?);",
        movie_genres_data,
    )
    print(f"[+] Inseridas {len(movie_genres_data):,} associações em 'movie_genres'.")
    conn.commit()


def load_movie_links(conn: sqlite3.Connection, raw_dir: str):
    """Processa link.csv e insere em movie_links (1:1)."""
    csv_path = os.path.join(raw_dir, "link.csv")
    print(f"\n[*] Lendo {csv_path}...")
    df = pd.read_csv(csv_path)

    links_data = []
    for _, row in df.iterrows():
        movie_id = int(row["movieId"])
        imdb_id = str(row["imdbId"]).zfill(7) if pd.notna(row["imdbId"]) else None
        tmdb_id = int(row["tmdbId"]) if pd.notna(row["tmdbId"]) else None
        links_data.append((movie_id, imdb_id, tmdb_id))

    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO movie_links (movie_id, imdb_id, tmdb_id) VALUES (?, ?, ?);",
        links_data,
    )
    conn.commit()
    print(f"[+] Inseridos {len(links_data):,} registros em 'movie_links'.")


def load_tags_and_users(conn: sqlite3.Connection, raw_dir: str) -> set:
    """
    3FN: Normaliza o vocabulário de tags de tag.csv em 'tags' e 'user_movie_tags'.
    Retorna o conjunto de user_ids encontrados.
    """
    csv_path = os.path.join(raw_dir, "tag.csv")
    print(f"\n[*] Lendo e normalizando {csv_path}...")
    df = pd.read_csv(csv_path)

    tag_to_id = {}
    tag_id_counter = 1
    user_ids = set()
    user_tags_data = []

    # Ordenar por timestamp para manter histórico ordenado
    df = df.dropna(subset=["tag"])

    for _, row in df.iterrows():
        uid = int(row["userId"])
        mid = int(row["movieId"])
        raw_tag = str(row["tag"]).strip().lower()
        ts = str(row["timestamp"])

        if not raw_tag:
            continue

        user_ids.add(uid)

        if raw_tag not in tag_to_id:
            tag_to_id[raw_tag] = tag_id_counter
            tag_id_counter += 1

        user_tags_data.append((uid, mid, tag_to_id[raw_tag], ts))

    cursor = conn.cursor()

    # 1. Inserir Catálogo de Tags
    tags_records = [(tid, name) for name, tid in sorted(tag_to_id.items(), key=lambda x: x[1])]
    cursor.executemany(
        "INSERT INTO tags (tag_id, tag_name) VALUES (?, ?);",
        tags_records,
    )
    print(f"[+] Inseridas {len(tags_records):,} tags únicas em 'tags'.")
    conn.commit()

    return user_ids, user_tags_data


def load_ratings_and_finalize_users(
    conn: sqlite3.Connection,
    raw_dir: str,
    tag_user_ids: set,
    user_tags_data: list,
    sample_ratings: int,
    all_ratings: bool,
):
    """
    Lê ratings.csv em chunks, cadastra todos os usuários em 'users',
    insere as tags de usuários em 'user_movie_tags' e as avaliações em 'ratings'.
    """
    csv_path = os.path.join(raw_dir, "rating.csv")
    print(f"\n[*] Processando avaliações de {csv_path}...")

    all_users = set(tag_user_ids)
    ratings_to_insert = []
    total_ratings_loaded = 0

    chunksize = 200000
    for chunk in pd.read_csv(csv_path, chunksize=chunksize):
        if not all_ratings and sample_ratings > 0:
            remaining = sample_ratings - total_ratings_loaded
            if remaining <= 0:
                break
            if len(chunk) > remaining:
                chunk = chunk.iloc[:remaining]

        # Coletar novos usuários
        all_users.update(chunk["userId"].unique().tolist())

        # Preparar tuplas para inserção
        tuples = [
            (int(r.userId), int(r.movieId), float(r.rating), str(r.timestamp))
            for r in chunk.itertuples(index=False)
        ]
        ratings_to_insert.extend(tuples)
        total_ratings_loaded += len(tuples)

        if not all_ratings and sample_ratings > 0 and total_ratings_loaded >= sample_ratings:
            break

        if len(ratings_to_insert) >= 500000:
            print(f"    - Acumulados {total_ratings_loaded:,} ratings...")

    cursor = conn.cursor()

    # 1. Inserir Usuários necessários na tabela 'users' para garantir integridade referencial
    print(f"[*] Inserindo {len(all_users):,} usuários na tabela 'users'...")
    user_records = [(uid,) for uid in sorted(all_users)]
    cursor.executemany("INSERT OR IGNORE INTO users (user_id) VALUES (?);", user_records)
    conn.commit()
    print(f"[+] Tabela 'users' populada com sucesso.")

    # 2. Inserir user_movie_tags
    print(f"[*] Inserindo {len(user_tags_data):,} registros em 'user_movie_tags'...")
    # Usar INSERT OR IGNORE para evitar duplicidades exatas no mesmo timestamp
    cursor.executemany(
        "INSERT OR IGNORE INTO user_movie_tags (user_id, movie_id, tag_id, tagged_at) VALUES (?, ?, ?, ?);",
        user_tags_data,
    )
    conn.commit()
    print(f"[+] Inseridos registros em 'user_movie_tags'.")

    # 3. Inserir Ratings
    print(f"[*] Inserindo {len(ratings_to_insert):,} avaliações em 'ratings'...")
    batch_size = 50000
    for i in range(0, len(ratings_to_insert), batch_size):
        batch = ratings_to_insert[i : i + batch_size]
        cursor.executemany(
            "INSERT OR IGNORE INTO ratings (user_id, movie_id, rating, rated_at) VALUES (?, ?, ?, ?);",
            batch,
        )
    conn.commit()
    print(f"[+] {total_ratings_loaded:,} avaliações inseridas com sucesso.")


def verify_relational_database(conn: sqlite3.Connection):
    """Executa checagem de integridade e exibe contagem de registros por tabela."""
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("VERIFICAÇÃO DE INTEGRIDADE E CONTAGEM DE DADOS (3FN)")
    print("=" * 60)

    # Checar violações de chaves estrangeiras
    cursor.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()
    if fk_violations:
        print(f"[!] ATENÇÃO: {len(fk_violations)} violações de chave estrangeira encontradas:")
        for v in fk_violations[:5]:
            print("   ", v)
    else:
        print("[OK] Todas as restrições de chave estrangeira atendidas (0 violações).")

    tables = [
        "users",
        "movies",
        "genres",
        "movie_genres",
        "movie_links",
        "tags",
        "user_movie_tags",
        "ratings",
    ]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"  - Tabela '{table}': {count:>10,} tuplas")

    print("=" * 60 + "\n")


def main():
    args = parse_args()
    start_time = time.time()

    print("=" * 70)
    print("ETL DO MOVIELENS - NORMALIZAÇÃO E CARGA RELACIONAL (3FN)")
    print(f"Origem dos CSVs : {args.raw_dir}")
    print(f"Destino SQLite  : {args.db_path}")
    print(f"Amostra Ratings : {'TODAS (20M)' if args.all_ratings else f'{args.sample_ratings:,} registros'}")
    print("=" * 70)

    # 1. Inicializar banco e esquema
    conn = init_database(args.db_path, args.schema_file)

    try:
        # 2. Filmes e Gêneros (1FN / 2FN)
        load_movies_and_genres(conn, args.raw_dir)

        # 3. Links externos (1:1)
        load_movie_links(conn, args.raw_dir)

        # 4. Tags e Usuários (3FN)
        tag_user_ids, user_tags_data = load_tags_and_users(conn, args.raw_dir)

        # 5. Ratings e carga de Usuários
        load_ratings_and_finalize_users(
            conn=conn,
            raw_dir=args.raw_dir,
            tag_user_ids=tag_user_ids,
            user_tags_data=user_tags_data,
            sample_ratings=args.sample_ratings,
            all_ratings=args.all_ratings,
        )

        # 6. Validação e estatísticas
        verify_relational_database(conn)

    finally:
        conn.close()

    elapsed = time.time() - start_time
    print(f"[+] Processo concluído com êxito em {elapsed:.2f} segundos!")


if __name__ == "__main__":
    main()
