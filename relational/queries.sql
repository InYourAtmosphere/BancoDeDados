-- =============================================================================
-- CONSULTAS DE BENCHMARK E VALIDAÇÃO - MODELO RELACIONAL (3FN)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Consulta 1: Detalhes de um filme específico (Requer múltiplos JOINs para
-- reconstruir o objeto que foi desmembrado na normalização)
-- -----------------------------------------------------------------------------
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

-- -----------------------------------------------------------------------------
-- Consulta 2: Top 10 filmes mais bem avaliados com no mínimo 50 avaliações
-- -----------------------------------------------------------------------------
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
LIMIT 10;

-- -----------------------------------------------------------------------------
-- Consulta 3: Quantidade de filmes e média de notas por Gênero
-- -----------------------------------------------------------------------------
SELECT 
    g.name AS genre,
    COUNT(DISTINCT m.movie_id) AS total_movies,
    ROUND(AVG(r.rating), 2) AS avg_genre_rating
FROM genres g
JOIN movie_genres mg ON g.genre_id = mg.genre_id
JOIN movies m ON mg.movie_id = m.movie_id
LEFT JOIN ratings r ON m.movie_id = r.movie_id
GROUP BY g.genre_id, g.name
ORDER BY total_movies DESC;

-- -----------------------------------------------------------------------------
-- Consulta 4: Buscar filmes marcados com tags específicas (ex: 'pixar' ou 'animation')
-- -----------------------------------------------------------------------------
SELECT DISTINCT
    m.movie_id,
    m.title,
    m.release_year,
    t.tag_name
FROM movies m
JOIN user_movie_tags umt ON m.movie_id = umt.movie_id
JOIN tags t ON umt.tag_id = t.tag_id
WHERE t.tag_name IN ('pixar', 'animation')
LIMIT 20;
