#!/usr/bin/env python3
"""
scripts/test_sql_queries.py
--------------------------------------------------------------------------------
Executa as 4 consultas de benchmark do modelo relacional (3FN) no SQLite
e exibe os resultados formatados no terminal para comparação com o NoSQL.
--------------------------------------------------------------------------------
"""

import sqlite3
import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)


def main():
    db_path = "relational/movielens.db"
    conn = sqlite3.connect(db_path)

    print("=" * 80)
    print("DEMONSTRAÇÃO DAS CONSULTAS RELACIONAIS (3FN) - SQLITE / POSTGRESQL")
    print(f"Banco de Dados: {db_path}")
    print("=" * 80)

    # Consulta 1
    print("\n>>> CONSULTA 1: Detalhes de um Filme (Toy Story) via 4 JOINs e GROUP BY")
    q1 = """
    SELECT 
        m.movie_id,
        m.title,
        m.release_year,
        l.imdb_id,
        l.tmdb_id,
        GROUP_CONCAT(DISTINCT g.name) AS genres,
        COUNT(r.rating) AS total_ratings,
        ROUND(AVG(r.rating), 2) AS avg_rating
    FROM movies m
    LEFT JOIN movie_links l ON m.movie_id = l.movie_id
    LEFT JOIN movie_genres mg ON m.movie_id = mg.movie_id
    LEFT JOIN genres g ON mg.genre_id = g.genre_id
    LEFT JOIN ratings r ON m.movie_id = r.movie_id
    WHERE m.movie_id = 1
    GROUP BY m.movie_id, m.title, m.release_year, l.imdb_id, l.tmdb_id;
    """
    df1 = pd.read_sql_query(q1, conn)
    print(df1.to_string(index=False))

    # Consulta 2
    print("\n>>> CONSULTA 2: Top 5 Filmes mais bem avaliados (mínimo de 50 votos)")
    q2 = """
    SELECT 
        m.movie_id,
        m.title,
        m.release_year,
        COUNT(r.rating) AS vote_count,
        ROUND(AVG(r.rating), 3) AS average_rating
    FROM movies m
    JOIN ratings r ON m.movie_id = r.movie_id
    GROUP BY m.movie_id, m.title, m.release_year
    HAVING COUNT(r.rating) >= 50
    ORDER BY average_rating DESC, vote_count DESC
    LIMIT 5;
    """
    df2 = pd.read_sql_query(q2, conn)
    print(df2.to_string(index=False))

    # Consulta 3
    print("\n>>> CONSULTA 3: Total de Filmes e Média de Notas por Gênero (JOIN N:M)")
    q3 = """
    SELECT 
        g.name AS genre,
        COUNT(DISTINCT m.movie_id) AS total_movies,
        ROUND(AVG(r.rating), 2) AS avg_genre_rating
    FROM genres g
    JOIN movie_genres mg ON g.genre_id = mg.genre_id
    JOIN movies m ON mg.movie_id = m.movie_id
    LEFT JOIN ratings r ON m.movie_id = r.movie_id
    GROUP BY g.genre_id, g.name
    ORDER BY total_movies DESC
    LIMIT 5;
    """
    df3 = pd.read_sql_query(q3, conn)
    print(df3.to_string(index=False))

    # Consulta 4
    print("\n>>> CONSULTA 4: Busca por Tags ('pixar' ou 'animation') via JOIN Triplo")
    q4 = """
    SELECT DISTINCT
        m.movie_id,
        m.title,
        m.release_year,
        t.tag_name
    FROM movies m
    JOIN user_movie_tags umt ON m.movie_id = umt.movie_id
    JOIN tags t ON umt.tag_id = t.tag_id
    WHERE t.tag_name IN ('pixar', 'animation')
    LIMIT 5;
    """
    df4 = pd.read_sql_query(q4, conn)
    print(df4.to_string(index=False))

    print("\n" + "=" * 80)
    conn.close()


if __name__ == "__main__":
    main()
