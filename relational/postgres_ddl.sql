-- =============================================================================
-- ESQUEMA RELACIONAL NORMALIZADO (3FN) - POSTGRESQL 14+
-- Projeto: Análise Comparativa Relacional vs. NoSQL (Dataset MovieLens)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. TABELA DE USUÁRIOS (users)
-- Ancoragem da integridade referencial para evitar registros órfãos.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
);

-- -----------------------------------------------------------------------------
-- 2. TABELA DE FILMES (movies)
-- 1FN: Título atômico com separação do ano de lançamento (release_year).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    release_year SMALLINT CHECK (release_year >= 1880 AND release_year <= 2100)
);

-- -----------------------------------------------------------------------------
-- 3. TABELA DE GÊNEROS (genres)
-- 1FN: Catálogo de gêneros únicos normalizados.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS genres (
    genre_id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- -----------------------------------------------------------------------------
-- 4. TABELA ASSOCIATIVA FILME <-> GÊNERO (movie_genres)
-- 1FN / 2FN: Resolve a relação N:M entre filmes e gêneros.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id INTEGER NOT NULL REFERENCES movies (movie_id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres (genre_id) ON DELETE CASCADE,
    CONSTRAINT pk_movie_genres PRIMARY KEY (movie_id, genre_id)
);

-- -----------------------------------------------------------------------------
-- 5. TABELA DE LINKS EXTERNOS (movie_links)
-- 3FN: Relação 1:1 que isola metadados externos (IMDb e TMDb).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movie_links (
    movie_id INTEGER PRIMARY KEY REFERENCES movies (movie_id) ON DELETE CASCADE,
    imdb_id VARCHAR(20),
    tmdb_id INTEGER
);

-- -----------------------------------------------------------------------------
-- 6. TABELA DE TAGS (tags)
-- 3FN: Elimina a repetição textual redundante dos rótulos de etiquetagem.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tags (
    tag_id INTEGER PRIMARY KEY,
    tag_name VARCHAR(255) NOT NULL UNIQUE
);

-- -----------------------------------------------------------------------------
-- 7. TABELA DE ETIQUETAGENS (user_movie_tags)
-- Registra as marcações feitas por usuários nos filmes.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_movie_tags (
    user_id INTEGER NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies (movie_id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags (tag_id) ON DELETE CASCADE,
    tagged_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    CONSTRAINT pk_user_movie_tags PRIMARY KEY (user_id, movie_id, tag_id, tagged_at)
);

-- -----------------------------------------------------------------------------
-- 8. TABELA DE AVALIAÇÕES (ratings)
-- 2FN / 3FN: Chave primária composta (user_id, movie_id).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ratings (
    user_id INTEGER NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies (movie_id) ON DELETE CASCADE,
    rating NUMERIC(2,1) NOT NULL CHECK (rating >= 0.5 AND rating <= 5.0),
    rated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    CONSTRAINT pk_ratings PRIMARY KEY (user_id, movie_id)
);

-- -----------------------------------------------------------------------------
-- ÍNDICES B-TREE ESPECÍFICOS PARA OTIMIZAÇÃO DE CONSULTAS (POSTGRESQL)
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_movies_release_year ON movies (release_year);
CREATE INDEX IF NOT EXISTS idx_ratings_movie_id ON ratings (movie_id);
CREATE INDEX IF NOT EXISTS idx_ratings_user_id ON ratings (user_id);
CREATE INDEX IF NOT EXISTS idx_user_movie_tags_movie_id ON user_movie_tags (movie_id);
CREATE INDEX IF NOT EXISTS idx_user_movie_tags_tag_id ON user_movie_tags (tag_id);

CREATE SEQUENCE IF NOT EXISTS genre_id_seq AS INTEGER 
OWNED BY genres.genre_id;

CREATE SEQUENCE IF NOT EXISTS tag_id_seq AS INTEGER 
OWNED BY tags.tag_id;

ALTER TABLE genres ALTER COLUMN genre_id SET DEFAULT NEXTVAL('genre_id_seq');
ALTER TABLE tags ALTER COLUMN tag_id SET DEFAULT NEXTVAL('tag_id_seq');