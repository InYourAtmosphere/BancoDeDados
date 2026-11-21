-- =============================================================================
-- CONSULTAS DE COMPARAÇÃO - MODELO RELACIONAL (3FN) - POSTGRESQL
-- Equivalentes, uma a uma, às de neo4j/queries.cypher.
-- Executável com: psql -h localhost -U postgres -d movielens -f relational/queries.sql
-- Os marcadores "-- name:" são lidos por scripts/test_sql_queries.py e scripts/benchmark.py.
-- =============================================================================


-- name: c1_ficha
-- titulo: Consulta 1 - Ficha completa de um filme (Toy Story)
-- As avaliações são agregadas numa subconsulta: juntá-las diretamente com
-- movie_genres multiplicaria cada avaliação pelo número de gêneros do filme.
SELECT
    m.movie_id,
    m.title,
    m.release_year,
    l.imdb_id,
    l.tmdb_id,
    (SELECT string_agg(g.name, ', ' ORDER BY g.name)
       FROM movie_genres mg JOIN genres g ON g.genre_id = mg.genre_id
      WHERE mg.movie_id = m.movie_id)                      AS genres,
    r.total_ratings,
    r.avg_rating
FROM movies m
LEFT JOIN movie_links l ON l.movie_id = m.movie_id
CROSS JOIN LATERAL (
    SELECT COUNT(*) AS total_ratings, ROUND(AVG(rating), 2) AS avg_rating
      FROM ratings WHERE movie_id = m.movie_id
) r
WHERE m.movie_id = 1;


-- name: c2_top10
-- titulo: Consulta 2 - Top 10 filmes mais bem avaliados (mínimo de 50 votos)
SELECT
    m.movie_id,
    m.title,
    m.release_year,
    COUNT(*)                AS vote_count,
    ROUND(AVG(r.rating), 3) AS average_rating
FROM movies m
JOIN ratings r ON r.movie_id = m.movie_id
GROUP BY m.movie_id, m.title, m.release_year
HAVING COUNT(*) >= 50
ORDER BY AVG(r.rating) DESC, vote_count DESC, m.movie_id
LIMIT 10;


-- name: c3_generos
-- titulo: Consulta 3 - Total de filmes e média das avaliações por gênero
-- A média é sobre todas as avaliações dos filmes do gênero (filmes com mais votos pesam mais).
SELECT
    g.name                       AS genre,
    COUNT(DISTINCT mg.movie_id)  AS total_movies,
    COUNT(r.rating)              AS total_ratings,
    ROUND(AVG(r.rating), 2)      AS avg_genre_rating
FROM genres g
JOIN movie_genres mg ON mg.genre_id = g.genre_id
LEFT JOIN ratings r  ON r.movie_id = mg.movie_id
GROUP BY g.genre_id, g.name
ORDER BY total_movies DESC, genre;


-- name: c4_tags
-- titulo: Consulta 4 - Filmes marcados com 'pixar' ou 'animation'
SELECT
    m.movie_id,
    m.title,
    m.release_year,
    string_agg(DISTINCT t.tag_name, ', ') AS matched_tags
FROM movies m
JOIN user_movie_tags umt ON umt.movie_id = m.movie_id
JOIN tags t              ON t.tag_id = umt.tag_id
WHERE t.tag_name IN ('pixar', 'animation')
GROUP BY m.movie_id, m.title, m.release_year
ORDER BY m.movie_id
LIMIT 20;


-- name: c5_recomendacao
-- titulo: Consulta 5 - "Quem gostou de Toy Story também gostou de..." (2 saltos)
-- Self-join da tabela ratings: usuários que deram >= 4 ao filme 1 e o que mais eles avaliaram bem.
SELECT
    m.movie_id,
    m.title,
    COUNT(*) AS score
FROM ratings r1
JOIN ratings r2 ON r2.user_id = r1.user_id
              AND r2.movie_id <> r1.movie_id
JOIN movies m   ON m.movie_id = r2.movie_id
WHERE r1.movie_id = 1
  AND r1.rating >= 4
  AND r2.rating >= 4
GROUP BY m.movie_id, m.title
ORDER BY score DESC, m.movie_id
LIMIT 10;


-- name: c6_similares_tags
-- titulo: Consulta 6 - Filmes com mais tags em comum com Toy Story
WITH movie_tag AS (
    SELECT DISTINCT movie_id, tag_id FROM user_movie_tags
)
SELECT
    m.movie_id,
    m.title,
    COUNT(*) AS tags_em_comum,
    string_agg(t.tag_name, ', ' ORDER BY t.tag_name) AS tags
FROM movie_tag a
JOIN movie_tag b ON b.tag_id = a.tag_id AND b.movie_id <> a.movie_id
JOIN movies m    ON m.movie_id = b.movie_id
JOIN tags t      ON t.tag_id = a.tag_id
WHERE a.movie_id = 1
GROUP BY m.movie_id, m.title
ORDER BY tags_em_comum DESC, m.movie_id
LIMIT 10;


-- name: c7_sugestao_genero
-- titulo: Consulta 7 - Sugestão por gênero: filmes parecidos com Toy Story (gêneros em comum, desempate por tags)
-- Candidatos: filmes que compartilham tags com Toy Story (self-join da tabela de tags, já
-- deduplicada). Ranking: nº de gêneros em comum e, no empate, nº de tags em comum.
WITH movie_tag AS (
    SELECT DISTINCT movie_id, tag_id FROM user_movie_tags
),
por_tag AS (
    SELECT b.movie_id, COUNT(*) AS tags
    FROM movie_tag a
    JOIN movie_tag b ON b.tag_id = a.tag_id AND b.movie_id <> a.movie_id
    WHERE a.movie_id = 1
    GROUP BY b.movie_id
)
SELECT
    m.movie_id,
    m.title,
    COUNT(DISTINCT mg.genre_id) AS generos_em_comum,
    t.tags                      AS tags_em_comum
FROM por_tag t
JOIN movies m        ON m.movie_id = t.movie_id
JOIN movie_genres mg ON mg.movie_id = m.movie_id
WHERE mg.genre_id IN (SELECT genre_id FROM movie_genres WHERE movie_id = 1)
GROUP BY m.movie_id, m.title, t.tags
ORDER BY generos_em_comum DESC, t.tags DESC, m.movie_id
LIMIT 10;
