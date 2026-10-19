#!/usr/bin/env python3
"""
scripts/test_nosql_queries.py
--------------------------------------------------------------------------------
Executa no MongoDB as 4 consultas equivalentes às do modelo relacional
(mesmas de mongodb/queries.js) e exibe os resultados no terminal.
--------------------------------------------------------------------------------
"""

import json

from pymongo import MongoClient

from common import MONGO_URI


def show(docs):
    print(json.dumps(list(docs), indent=2, ensure_ascii=False, default=str))


def main():
    db = MongoClient(MONGO_URI, serverSelectionTimeoutMS=4000).movielens

    print("=" * 70)
    print("DEMONSTRAÇÃO DAS CONSULTAS DOCUMENTAIS - MONGODB")
    print("=" * 70)

    print("\n>>> CONSULTA 1: Detalhes de um Filme (Embedding vs 4 JOINs do SQL)")
    show([db.movies.find_one({"_id": 1})])

    print("\n>>> CONSULTA 2: Top 5 Filmes mais bem avaliados (com no mínimo 50 votos)")
    show(db.movies.find(
        {"metrics.rating_count": {"$gte": 50}},
        {"title": 1, "release_year": 1, "metrics": 1},
    ).sort([("metrics.avg_rating", -1), ("metrics.rating_count", -1)]).limit(5))

    print("\n>>> CONSULTA 3: Total de Filmes e Média de Nota por Gênero ($unwind)")
    show(db.movies.aggregate([
        {"$unwind": "$genres"},
        {"$group": {"_id": "$genres", "total_movies": {"$sum": 1},
                    "avg_genre_rating": {"$avg": "$metrics.avg_rating"}}},
        {"$project": {"_id": 0, "genre": "$_id", "total_movies": 1,
                      "avg_genre_rating": {"$round": ["$avg_genre_rating", 2]}}},
        {"$sort": {"total_movies": -1}},
        {"$limit": 5},
    ]))

    print("\n>>> CONSULTA 4: Busca por Tags com Operador $in (Índice Multikey)")
    show(db.movies.find(
        {"tags": {"$in": ["pixar", "animation"]}},
        {"title": 1, "release_year": 1, "genres": 1, "tags": 1},
    ).limit(5))

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
