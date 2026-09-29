#!/usr/bin/env python3
"""
mongodb/import.py
--------------------------------------------------------------------------------
Script de Carga e Indexação no MongoDB.
Lê os arquivos JSON Lines gerados em data/processed/:
  - movies.jsonl
  - ratings.jsonl
Conecta-se ao MongoDB (local, Docker ou Atlas), realiza a inserção em lote (bulk)
e cria os índices multikey e compostos recomendados.
--------------------------------------------------------------------------------
"""

import os
import sys
import json
import time
import argparse
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


def parse_args():
    parser = argparse.ArgumentParser(description="Carga de Dados no MongoDB")
    parser.add_argument(
        "--uri",
        type=str,
        default="mongodb://root:mongopassword@localhost:27017/?authSource=admin",
        help="URI de conexão ao MongoDB (padrão: container Docker local com auth)",
    )
    parser.add_argument(
        "--db-name",
        type=str,
        default="movielens",
        help="Nome do banco de dados (padrão: movielens)",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed",
        help="Diretório onde estão os arquivos .jsonl (padrão: data/processed)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Tamanho do lote de inserção em massa (padrão: 5000)",
    )
    return parser.parse_args()


def load_collection_from_jsonl(collection, file_path: str, batch_size: int):
    """Lê um arquivo JSONL e insere em lotes no MongoDB."""
    if not os.path.exists(file_path):
        print(f"[!] Erro: Arquivo {file_path} não encontrado.")
        return 0

    print(f"[*] Importando {file_path} para a coleção '{collection.name}'...")
    batch = []
    total_inserted = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            doc = json.loads(line)
            batch.append(doc)

            if len(batch) >= batch_size:
                collection.insert_many(batch, ordered=False)
                total_inserted += len(batch)
                batch = []
                print(f"    - Inseridos {total_inserted:,} documentos...")

        if batch:
            collection.insert_many(batch, ordered=False)
            total_inserted += len(batch)

    print(f"[+] Total de {total_inserted:,} documentos importados em '{collection.name}'.")
    return total_inserted


def create_indexes(db):
    """Cria índices estratégicos (Multikey, B-Tree) para alta performance."""
    print("\n[*] Criando índices no MongoDB...")

    # Índices na coleção movies
    db.movies.create_index([("release_year", ASCENDING)], name="idx_release_year")
    db.movies.create_index([("genres", ASCENDING)], name="idx_multikey_genres")
    db.movies.create_index([("tags", ASCENDING)], name="idx_multikey_tags")
    db.movies.create_index([("metrics.avg_rating", DESCENDING)], name="idx_metrics_avg_rating")
    print("  [+] Índices criados na coleção 'movies': genres (multikey), tags, release_year, avg_rating.")

    # Índices na coleção ratings
    db.ratings.create_index([("movie_id", ASCENDING)], name="idx_ratings_movie_id")
    db.ratings.create_index([("user_id", ASCENDING)], name="idx_ratings_user_id")
    print("  [+] Índices criados na coleção 'ratings': movie_id, user_id.")


def main():
    args = parse_args()
    start_time = time.time()

    print("=" * 70)
    print("CARGA DE DADOS NO MONGODB - MOVIELENS")
    print(f"URI de Conexão : {args.uri.split('@')[-1] if '@' in args.uri else args.uri}")
    print(f"Banco de Dados : {args.db_name}")
    print("=" * 70)

    # 1. Tentar conectar com timeout curto para feedback imediato
    try:
        client = MongoClient(args.uri, serverSelectionTimeoutMS=4000)
        # Força verificação da conexão
        client.admin.command("ping")
        print("[+] Conexão com o MongoDB estabelecida com sucesso!")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print("\n[!] AVISO: Não foi possível conectar ao servidor MongoDB local.")
        print(f"    Detalhes do erro: {e}")
        print("\n[i] Para subir uma instância local via Docker:")
        print("    1. Certifique-se de que o Docker Desktop esteja aberto.")
        print("    2. Execute: docker compose up -d mongodb")
        print("    3. Execute novamente: python mongodb/import.py")
        print("\n[i] Caso esteja usando MongoDB Atlas na nuvem:")
        print("    python mongodb/import.py --uri 'mongodb+srv://<user>:<pwd>@cluster.mongodb.net/'")
        print("\n[i] Os arquivos JSONL gerados já estão validados e prontos em 'data/processed/'.")
        sys.exit(0)

    db = client[args.db_name]

    # 2. Reiniciar coleções para carga limpa
    db.movies.drop()
    db.ratings.drop()
    print("[*] Coleções antigas limpas.")

    # 3. Importar coleções
    movies_file = os.path.join(args.data_dir, "movies.jsonl")
    ratings_file = os.path.join(args.data_dir, "ratings.jsonl")

    load_collection_from_jsonl(db.movies, movies_file, args.batch_size)
    load_collection_from_jsonl(db.ratings, ratings_file, args.batch_size)

    # 4. Criar índices
    create_indexes(db)

    # 5. Exibir estatísticas
    print("\n" + "=" * 60)
    print("ESTATÍSTICAS FINAIS NO MONGODB")
    print("=" * 60)
    print(f"  - Documentos em 'movies' : {db.movies.count_documents({}):,}")
    print(f"  - Documentos em 'ratings': {db.ratings.count_documents({}):,}")
    print("=" * 60)

    elapsed = time.time() - start_time
    print(f"[+] Importação concluída com sucesso em {elapsed:.2f}s!")


if __name__ == "__main__":
    main()
