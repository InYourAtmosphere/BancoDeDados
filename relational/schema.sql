-- =============================================================================
-- ESQUEMA RELACIONAL NORMALIZADO (3FN) - MOVIELENS
-- Compatibilidade: PostgreSQL (9.5+) e SQLite (3.24+)
-- =============================================================================

-- Habilita verificação de integridade referencial (específico para sessões SQLite)
PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- 1. TABELA DE USUÁRIOS
-- Representa a entidade mestre dos usuários do sistema.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
);

-- -----------------------------------------------------------------------------
-- 2. TABELA DE FILMES
-- 1FN: Título atômico com separação do ano de lançamento (release_year).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    release_year SMALLINT
);

-- -----------------------------------------------------------------------------
-- 3. TABELA DE GÊNEROS (CATÁLOGO)
-- 1FN: Cada gênero é uma tupla única e atômica.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS genres (
    genre_id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- -----------------------------------------------------------------------------
-- 4. TABELA ASSOCIATIVA FILME <-> GÊNERO (N:M)
-- 1FN/2FN: Resolve a relação de muitos-para-muitos entre filmes e gêneros.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (movie_id, genre_id),
    FOREIGN KEY (movie_id) REFERENCES movies (movie_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres (genre_id) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- 5. TABELA DE LINKS EXTERNOS (IMDb / TMDb - Relação 1:1)
-- 3FN: Isola identificadores externos de catálogos de terceiros.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movie_links (
    movie_id INTEGER PRIMARY KEY,
    imdb_id VARCHAR(20),
    tmdb_id INTEGER,
    FOREIGN KEY (movie_id) REFERENCES movies (movie_id) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- 6. TABELA DE TAGS (CATÁLOGO NORMALIZADO)
-- 3FN: Elimina a repetição redundante das strings textuais de tags.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tags (
    tag_id INTEGER PRIMARY KEY,
    tag_name VARCHAR(255) NOT NULL UNIQUE
);

-- -----------------------------------------------------------------------------
-- 7. TABELA DE ETIQUETAGENS DE USUÁRIOS
-- Registra a associação de etiquetagem (user_id, movie_id, tag_id, timestamp).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_movie_tags (
    user_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    tagged_at TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, movie_id, tag_id, tagged_at),
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies (movie_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags (tag_id) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- 8. TABELA DE AVALIAÇÕES (RATINGS)
-- 2FN/3FN: Chave composta (user_id, movie_id).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ratings (
    user_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL,
    rating NUMERIC(2,1) NOT NULL CHECK (rating >= 0.5 AND rating <= 5.0),
    rated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, movie_id),
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies (movie_id) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- ÍNDICES PARA OTIMIZAÇÃO DE CONSULTAS FREQUENTES
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_movies_year ON movies (release_year);
CREATE INDEX IF NOT EXISTS idx_movie_genres_genre ON movie_genres (genre_id);
CREATE INDEX IF NOT EXISTS idx_ratings_movie ON ratings (movie_id);
CREATE INDEX IF NOT EXISTS idx_ratings_user ON ratings (user_id);
CREATE INDEX IF NOT EXISTS idx_user_movie_tags_movie ON user_movie_tags (movie_id);
CREATE INDEX IF NOT EXISTS idx_user_movie_tags_tag ON user_movie_tags (tag_id);
