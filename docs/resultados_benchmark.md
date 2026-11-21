# Resultados do Benchmark: PostgreSQL vs. Neo4j

- Data: 2026-11-20 20:47
- Máquina: Linux x86_64, Python 3.11.16
- Avaliações carregadas: 100,000
- Método: 1 execução de aquecimento + mediana de 5 execuções; timeout de 60s por execução.

| Consulta | PostgreSQL (ms) | Neo4j (ms) | Mais rápido |
| :--- | ---: | ---: | :---: |
| Consulta 1 - Ficha completa de um filme (Toy Story) | 0.8 | 3.1 | PostgreSQL |
| Consulta 2 - Top 10 filmes mais bem avaliados (mínimo de 50 votos) | 25.1 | 33.1 | PostgreSQL |
| Consulta 3 - Total de filmes e média das avaliações por gênero | 178.8 | 119.0 | Neo4j |
| Consulta 4 - Filmes marcados com 'pixar' ou 'animation' | 4.2 | 6.8 | PostgreSQL |
| Consulta 5 - "Quem gostou de Toy Story também gostou de..." (2 saltos) | 13.4 | 25.5 | PostgreSQL |
| Consulta 6 - Filmes com mais tags em comum com Toy Story | 135.9 | 11.7 | Neo4j |
| Consulta 7 - Menor distância de Toy Story (1) até The Godfather (858) via tags em comum | 4,536 | 2.2 | Neo4j |
