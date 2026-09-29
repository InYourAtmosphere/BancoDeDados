-- =============================================================================
-- SCRIPT DE CARGA NATIVA DE ALTA VELOCIDADE NO POSTGRESQL (COMANDO \copy)
-- Execução recomendada via terminal psql:
-- psql -h localhost -U postgres -d movielens -f relational/load_postgres.sql
-- =============================================================================

-- Desativa temporariamente a verificação de triggers e constraints para carga em massa ultra-rápida
SET session_replication_role = 'replica';

-- -----------------------------------------------------------------------------
-- 1. TABELAS DE STAGING (Área de transição para tratar dados brutos no Postgres)
-- -----------------------------------------------------------------------------
CREATE TEMP TABLE staging_movies (
    movie_id INT,
    title TEXT,
    genres TEXT
);

CREATE TEMP TABLE staging_links (
    movie_id INT,
    imdb_id TEXT,
    tmdb_id INT
);

CREATE TEMP TABLE staging_tags (
    user_id INT,
    movie_id INT,
    tag TEXT,
    timestamp TIMESTAMP WITHOUT TIME ZONE
);

CREATE TEMP TABLE staging_ratings (
    user_id INT,
    movie_id INT,
    rating NUMERIC(2,1),
    timestamp TIMESTAMP WITHOUT TIME ZONE
);

-- -----------------------------------------------------------------------------
-- 2. CARGA BRUTA DOS CSVS PARA STAGING
-- -----------------------------------------------------------------------------
\copy staging_movies FROM 'data/raw/movie.csv' WITH (FORMAT csv, HEADER true);
\copy staging_links FROM 'data/raw/link.csv' WITH (FORMAT csv, HEADER true);
\copy staging_tags FROM 'data/raw/tag.csv' WITH (FORMAT csv, HEADER true);
-- Para carga de amostra ou completa do rating:
\copy staging_ratings FROM 'data/raw/rating.csv' WITH (FORMAT csv, HEADER true);

-- -----------------------------------------------------------------------------
-- 3. NORMALIZAÇÃO DIRETA VIA SQL (1FN, 2FN, 3FN) NO POSTGRESQL
-- -----------------------------------------------------------------------------

-- Inserir Filmes atomizando título e ano via Regex nativo do PostgreSQL (1FN)
INSERT INTO movies (movie_id, title, release_year)
SELECT 
    movie_id,
    TRIM(REGEXP_REPLACE(title, '\s*\(\d{4}\)$', '')) AS title,
    NULLIF(SUBSTRING(title FROM '\((\d{4})\)$'), '')::SMALLINT AS release_year
FROM staging_movies
ON CONFLICT (movie_id) DO NOTHING;

-- Inserir Gêneros Únicos atomizando a coluna multivalorada (1FN)
INSERT INTO genres (name)
SELECT DISTINCT TRIM(unnest(string_to_array(genres, '|')))
FROM staging_movies
WHERE genres IS NOT NULL AND genres <> '(no genres listed)'
ON CONFLICT (name) DO NOTHING;

-- Inserir Tabela Associativa N:M movie_genres
INSERT INTO movie_genres (movie_id, genre_id)
SELECT DISTINCT 
    sm.movie_id,
    g.genre_id
FROM (
    SELECT movie_id, TRIM(unnest(string_to_array(genres, '|'))) AS genre_name
    FROM staging_movies
) sm
JOIN genres g ON sm.genre_name = g.name
ON CONFLICT DO NOTHING;

-- Inserir Links (1:1)
INSERT INTO movie_links (movie_id, imdb_id, tmdb_id)
SELECT 
    movie_id,
    LPAD(imdb_id, 7, '0'),
    tmdb_id
FROM staging_links
ON CONFLICT (movie_id) DO NOTHING;

-- Inserir Catálogo de Tags Normalizadas (3FN)
INSERT INTO tags (tag_name)
SELECT DISTINCT LOWER(TRIM(tag))
FROM staging_tags
WHERE tag IS NOT NULL AND TRIM(tag) <> ''
ON CONFLICT (tag_name) DO NOTHING;

-- Inserir Usuários (Garantir integridade referencial)
INSERT INTO users (user_id)
SELECT DISTINCT user_id FROM staging_tags
UNION
SELECT DISTINCT user_id FROM staging_ratings
ON CONFLICT (user_id) DO NOTHING;

-- Inserir Associações de Tags
INSERT INTO user_movie_tags (user_id, movie_id, tag_id, tagged_at)
SELECT DISTINCT
    st.user_id,
    st.movie_id,
    t.tag_id,
    st.timestamp
FROM staging_tags st
JOIN tags t ON LOWER(TRIM(st.tag)) = t.tag_name
WHERE st.tag IS NOT NULL
ON CONFLICT DO NOTHING;

-- Inserir Avaliações
INSERT INTO ratings (user_id, movie_id, rating, rated_at)
SELECT 
    user_id,
    movie_id,
    rating,
    timestamp
FROM staging_ratings
ON CONFLICT (user_id, movie_id) DO NOTHING;

-- Restaura o modo normal de replicação/constraints
SET session_replication_role = 'default';

-- Limpeza da área de staging
DROP TABLE staging_movies;
DROP TABLE staging_links;
DROP TABLE staging_tags;
DROP TABLE staging_ratings;

-- Atualizar estatísticas do otimizador de consultas (Cost-Based Optimizer)
ANALYZE;
