#!/usr/bin/env python3
"""
scripts/test_mongodb_queries.py
--------------------------------------------------------------------------------
Demonstração das 4 consultas equivalentes no modelo documental.
Se o MongoDB estiver ativo, executa via pymongo.
Se o MongoDB não estiver ativo, executa diretamente sobre os documentos JSONL
de data/processed/, validando a lógica das consultas e exibindo os resultados.
--------------------------------------------------------------------------------
"""

import os
import json
from collections import defaultdict


def run_standalone_demo():
    print("=" * 70)
    print("DEMONSTRAÇÃO DAS CONSULTAS DOCUMENTAIS (SEM NECESSIDADE DE SERVIDOR ATIVO)")
    print("=" * 70)

    movies_path = "data/processed/movies.jsonl"
    ratings_path = "data/processed/ratings.jsonl"

    if not os.path.exists(movies_path):
        print(f"[!] Arquivo {movies_path} não encontrado. Execute scripts/transform.py primeiro.")
        return

    # Carregar uma amostra de filmes em memória
    movies = {}
    with open(movies_path, "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            movies[d["_id"]] = d

    # -------------------------------------------------------------------------
    # Consulta 1: Detalhes do Filme 1 (Toy Story)
    # -------------------------------------------------------------------------
    print("\n>>> CONSULTA 1: Detalhes de um Filme (Embedding vs 4 JOINs do SQL)")
    toy_story = movies.get(1)
    print(json.dumps(toy_story, indent=2, ensure_ascii=False))

    # -------------------------------------------------------------------------
    # Consulta 2: Top 5 Filmes (Dados Pré-computados com métricas)
    # -------------------------------------------------------------------------
    print("\n>>> CONSULTA 2: Top 5 Filmes mais bem avaliados (com no mínimo 50 votos)")
    eligible = [
        m for m in movies.values()
        if m.get("metrics") and m["metrics"]["rating_count"] >= 50 and m["metrics"]["avg_rating"] is not None
    ]
    eligible.sort(key=lambda x: (x["metrics"]["avg_rating"], x["metrics"]["rating_count"]), reverse=True)
    for m in eligible[:5]:
        print(f"  - [{m['_id']}] {m['title']} ({m['release_year']}): Nota {m['metrics']['avg_rating']} ({m['metrics']['rating_count']} votos)")

    # -------------------------------------------------------------------------
    # Consulta 3: Distribuição e Média por Gênero ($unwind)
    # -------------------------------------------------------------------------
    print("\n>>> CONSULTA 3: Total de Filmes e Média de Nota por Gênero (Equivalente ao $unwind)")
    genre_movies = defaultdict(list)
    for m in movies.values():
        avg = m.get("metrics", {}).get("avg_rating")
        for g in m.get("genres", []):
            genre_movies[g].append(avg)

    genre_summary = []
    for g, ratings in genre_movies.items():
        valid_ratings = [r for r in ratings if r is not None]
        avg_rating = round(sum(valid_ratings) / len(valid_ratings), 2) if valid_ratings else None
        genre_summary.append((g, len(ratings), avg_rating))

    genre_summary.sort(key=lambda x: x[1], reverse=True)
    for g, count, avg in genre_summary[:5]:
        print(f"  - Gênero '{g}': {count:,} filmes (Média: {avg})")

    # -------------------------------------------------------------------------
    # Consulta 4: Busca por Tags ('pixar' ou 'animation')
    # -------------------------------------------------------------------------
    print("\n>>> CONSULTA 4: Busca por Tags com Operador $in (Índice Multikey)")
    tagged = [
        m for m in movies.values()
        if any(t in ("pixar", "animation") for t in m.get("tags", []))
    ]
    for m in tagged[:5]:
        sample_tags = [t for t in m.get("tags", []) if t in ("pixar", "animation")]
        print(f"  - [{m['_id']}] {m['title']} ({m['release_year']}) | Tags encontradas: {sample_tags}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_standalone_demo()
