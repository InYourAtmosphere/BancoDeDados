# Resultados do Benchmark: PostgreSQL vs. Neo4j

- Data: 2026-11-21 13:12
- Máquina: Linux x86_64, Python 3.14.10
- Avaliações carregadas: 100,000
- Método: 1 execução de aquecimento + mediana de 5 execuções; timeout de 60s por execução.

| Consulta | PostgreSQL (ms) | Neo4j (ms) | Mais rápido |
| :--- | ---: | ---: | :---: |
| Consulta 1 - Ficha completa de um filme (Toy Story) | 0.8 | 3.5 | PostgreSQL |
| Consulta 2 - Top 10 filmes mais bem avaliados (mínimo de 50 votos) | 41.5 | 55.2 | PostgreSQL |
| Consulta 3 - Total de filmes e média das avaliações por gênero | 260.0 | 218.8 | Neo4j |
| Consulta 4 - Filmes marcados com 'pixar' ou 'animation' | 4.9 | 4.8 | empate |
| Consulta 5 - "Quem gostou de Toy Story também gostou de..." (2 saltos) | 19.1 | 38.2 | PostgreSQL |
| Consulta 6 - Filmes com mais tags em comum com Toy Story | 230.0 | 17.4 | Neo4j |
| Consulta 7 - Sugestão por gênero: filmes parecidos com Toy Story (gêneros em comum, desempate por tags) | 208.2 | 72.1 | Neo4j |
