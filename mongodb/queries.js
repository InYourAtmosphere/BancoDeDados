// =============================================================================
// CONSULTAS EQUIVALENTES DE BENCHMARK NO MONGODB (MQL & AGGREGATION PIPELINE)
// Executável via mongosh:
// mongosh "mongodb://localhost:27017/movielens" mongodb/queries.js
// =============================================================================

// -----------------------------------------------------------------------------
// Consulta 1: Detalhes de um filme específico (Embedding vs. JOINs)
// No modelo relacional, foram necessários 4 JOINs e GROUP BY.
// No MongoDB, é uma busca direta O(1) pelo _id, trazendo o objeto completo!
// -----------------------------------------------------------------------------
print("=== CONSULTA 1: Detalhes do Filme (Toy Story) via Busca por Chave Primária ===");
const movie1 = db.movies.findOne(
    { _id: 1 },
    { title: 1, release_year: 1, genres: 1, links: 1, metrics: 1 }
);
printjson(movie1);


// -----------------------------------------------------------------------------
// Consulta 2: Top 10 filmes mais bem avaliados (com no mínimo 50 avaliações)
// Abordagem A: Consulta instantânea nos dados pré-computados (Padrão Computed)
// -----------------------------------------------------------------------------
print("\n=== CONSULTA 2A: Top 10 Filmes (Dados Pré-computados na Coleção 'movies') ===");
const topMoviesPrecomputed = db.movies.find(
    { "metrics.rating_count": { $gte: 50 } },
    { title: 1, release_year: 1, "metrics.avg_rating": 1, "metrics.rating_count": 1 }
).sort({ "metrics.avg_rating": -1, "metrics.rating_count": -1 }).limit(10).toArray();
printjson(topMoviesPrecomputed);


// -----------------------------------------------------------------------------
// Consulta 2B: Top 10 Filmes calculado em tempo real via Aggregation Pipeline
// Demonstra o uso de $group, $match, $sort, $limit e $lookup (equivalente ao JOIN)
// -----------------------------------------------------------------------------
print("\n=== CONSULTA 2B: Top 10 Filmes Calculado Dinamicamente na Coleção 'ratings' ===");
const topMoviesDynamic = db.ratings.aggregate([
    {
        $group: {
            _id: "$movie_id",
            avg_rating: { $avg: "$rating" },
            vote_count: { $sum: 1 }
        }
    },
    {
        $match: {
            vote_count: { $gte: 50 }
        }
    },
    {
        $sort: {
            avg_rating: -1,
            vote_count: -1
        }
    },
    {
        $limit: 10
    },
    {
        $lookup: {
            from: "movies",
            localField: "_id",
            foreignField: "_id",
            as: "movie"
        }
    },
    {
        $unwind: "$movie"
    },
    {
        $project: {
            _id: 1,
            title: "$movie.title",
            release_year: "$movie.release_year",
            avg_rating: { $round: ["$avg_rating", 3] },
            vote_count: 1
        }
    }
]).toArray();
printjson(topMoviesDynamic);


// -----------------------------------------------------------------------------
// Consulta 3: Quantidade de filmes e média de notas por Gênero
// Demonstra $unwind para desmembrar o array de gêneros embutidos
// -----------------------------------------------------------------------------
print("\n=== CONSULTA 3: Distribuição e Médias por Gênero ($unwind e $group) ===");
const genreStats = db.movies.aggregate([
    { $unwind: "$genres" },
    {
        $group: {
            _id: "$genres",
            total_movies: { $sum: 1 },
            avg_genre_rating: { $avg: "$metrics.avg_rating" }
        }
    },
    {
        $project: {
            genre: "$_id",
            _id: 0,
            total_movies: 1,
            avg_genre_rating: { $round: ["$avg_genre_rating", 2] }
        }
    },
    { $sort: { total_movies: -1 } }
]).toArray();
printjson(genreStats.slice(0, 5));


// -----------------------------------------------------------------------------
// Consulta 4: Buscar filmes marcados com tags específicas ('pixar' ou 'animation')
// Utiliza o índice Multikey nativo no array de tags com o operador $in
// -----------------------------------------------------------------------------
print("\n=== CONSULTA 4: Busca por Tags com Operador $in (Índice Multikey) ===");
const taggedMovies = db.movies.find(
    { tags: { $in: ["pixar", "animation"] } },
    { title: 1, release_year: 1, genres: 1, tags: 1 }
).limit(5).toArray();
printjson(taggedMovies);
