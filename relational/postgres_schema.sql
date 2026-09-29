-- =============================================================================
-- ESQUEMA RELACIONAL NORMALIZADO (3FN) - POSTGRESQL 14+
-- Projeto: Análise Comparativa Relacional vs. NoSQL (Dataset MovieLens)
-- =============================================================================

-- Limpeza prévia (caso já existam objetos com os mesmos nomes)
DROP TABLE IF EXISTS ratings CASCADE;
DROP TABLE IF EXISTS user_movie_tags CASCADE;
DROP TABLE IF EXISTS tags CASCADE;
DROP TABLE IF EXISTS movie_links CASCADE;
DROP TABLE IF EXISTS movie_genres CASCADE;
DROP TABLE IF EXISTS genres CASCADE;
DROP TABLE IF EXISTS movies CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- -----------------------------------------------------------------------------
-- 1. TABELA DE USUÁRIOS (users)
-- Ancoragem da integridade referencial para evitar registros órfãos.
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY
);

COMMENT ON TABLE users IS 'Entidade mestre dos usuários avaliadores da plataforma';
COMMENT ON COLUMN users.user_id IS 'Identificador único do usuário no MovieLens';

-- -----------------------------------------------------------------------------
-- 2. TABELA DE FILMES (movies)
-- 1FN: Título atômico com separação do ano de lançamento (release_year).
-- -----------------------------------------------------------------------------
CREATE TABLE movies (
    movie_id INTEGER PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    release_year SMALLINT CHECK (release_year >= 1880 AND release_year <= 2100)
);

COMMENT ON TABLE movies IS 'Catálogo principal de filmes com atributos atômicos (1FN)';
COMMENT ON COLUMN movies.movie_id IS 'Identificador único do filme';
COMMENT ON COLUMN movies.title IS 'Título da obra cinematográfica';
COMMENT ON COLUMN movies.release_year IS 'Ano de lançamento (extraído do título para indexação direta)';

-- -----------------------------------------------------------------------------
-- 3. TABELA DE GÊNEROS (genres)
-- 1FN: Catálogo de gêneros únicos normalizados.
-- -----------------------------------------------------------------------------
CREATE TABLE genres (
    genre_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

COMMENT ON TABLE genres IS 'Dicionário canônico de gêneros cinematográficos';

-- -----------------------------------------------------------------------------
-- 4. TABELA ASSOCIATIVA FILME <-> GÊNERO (movie_genres)
-- 1FN / 2FN: Resolve a relação N:M entre filmes e gêneros.
-- -----------------------------------------------------------------------------
CREATE TABLE movie_genres (
    movie_id INTEGER NOT NULL REFERENCES movies (movie_id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres (genre_id) ON DELETE CASCADE,
    CONSTRAINT pk_movie_genres PRIMARY KEY (movie_id, genre_id)
);

COMMENT ON TABLE movie_genres IS 'Tabela associativa N:M que mapeia os gêneros de cada filme';

-- -----------------------------------------------------------------------------
-- 5. TABELA DE LINKS EXTERNOS (movie_links)
-- 3FN: Relação 1:1 que isola metadados externos (IMDb e TMDb).
-- -----------------------------------------------------------------------------
CREATE TABLE movie_links (
    movie_id INTEGER PRIMARY KEY REFERENCES movies (movie_id) ON DELETE CASCADE,
    imdb_id VARCHAR(20),
    tmdb_id INTEGER
);

COMMENT ON TABLE movie_links IS 'Chaves externas para cruzamento com bases do IMDb e TMDb';

-- -----------------------------------------------------------------------------
-- 6. TABELA DE TAGS (tags)
-- 3FN: Elimina a repetição textual redundante dos rótulos de etiquetagem.
-- -----------------------------------------------------------------------------
CREATE TABLE tags (
    tag_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tag_name VARCHAR(255) NOT NULL UNIQUE
);

COMMENT ON TABLE tags IS 'Dicionário normalizado de tags livres sem repetição redundante';

-- -----------------------------------------------------------------------------
-- 7. TABELA DE ETIQUETAGENS (user_movie_tags)
-- Registra as marcações feitas por usuários nos filmes.
-- -----------------------------------------------------------------------------
CREATE TABLE user_movie_tags (
    user_id INTEGER NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies (movie_id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags (tag_id) ON DELETE CASCADE,
    tagged_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    CONSTRAINT pk_user_movie_tags PRIMARY KEY (user_id, movie_id, tag_id, tagged_at)
);

COMMENT ON TABLE user_movie_tags IS 'Histórico de etiquetagens atribuídas por usuários aos filmes';

-- -----------------------------------------------------------------------------
-- 8. TABELA DE AVALIAÇÕES (ratings)
-- 2FN / 3FN: Chave primária composta (user_id, movie_id).
-- -----------------------------------------------------------------------------
CREATE TABLE ratings (
    user_id INTEGER NOT NULL REFERENCES users (user_id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies (movie_id) ON DELETE CASCADE,
    rating NUMERIC(2,1) NOT NULL CHECK (rating >= 0.5 AND rating <= 5.0),
    rated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    CONSTRAINT pk_ratings PRIMARY KEY (user_id, movie_id)
);

COMMENT ON TABLE ratings IS 'Avaliações de usuários para filmes (escala de 0.5 a 5.0)';

-- -----------------------------------------------------------------------------
-- ÍNDICES B-TREE ESPECÍFICOS PARA OTIMIZAÇÃO DE CONSULTAS (POSTGRESQL)
-- -----------------------------------------------------------------------------
CREATE INDEX idx_movies_release_year ON movies (release_year);
CREATE INDEX idx_movie_genres_genre_id ON movie_genres (genre_id);
CREATE INDEX idx_ratings_movie_id ON ratings (movie_id);
CREATE INDEX idx_ratings_user_id ON ratings (user_id);
CREATE INDEX idx_user_movie_tags_movie_id ON user_movie_tags (movie_id);
CREATE INDEX idx_user_movie_tags_tag_id ON user_movie_tags (tag_id);
