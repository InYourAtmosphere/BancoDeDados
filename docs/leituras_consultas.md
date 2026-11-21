# Leituras das consultas

Texto de apoio para quem apresenta os slides das consultas (antes ficava no card "Leitura" de cada slide).
Tempos: mediana em ms, amostra de 100 mil avaliações.

## Consulta 1 · Ficha completa de um filme

*Quais são os dados, os gêneros e a nota média de Toy Story?*

- PostgreSQL: 0,8 ms · Neo4j: 3,1 ms · mais rápido: PostgreSQL, 3,9× mais rápido

Busca por chave nos dois bancos, e a diferença é de 2 ms. No SQL, juntar gêneros e notas no mesmo FROM multiplicaria as 241 notas pelos 5 gêneros; por isso a subconsulta LATERAL. No Cypher, o collect() antes de expandir evita o problema.

## Consulta 2 · Top 10 filmes (mín. 50 votos)

*Quais são os 10 filmes de maior média entre os que têm pelo menos 50 votos?*

- PostgreSQL: 25 ms · Neo4j: 33 ms · mais rápido: PostgreSQL, 1,3× mais rápido

Agregação sobre todas as avaliações. O PostgreSQL varre a tabela ratings, contígua e compacta, e agrupa com hash aggregate. O Neo4j visita as arestas RATED uma a uma. Lidera The Maltese Falcon (4,44, com 59 votos).

## Consulta 3 · Filmes e média por gênero

*Quantos filmes e qual a nota média de cada um dos 19 gêneros?*

- PostgreSQL: 179 ms · Neo4j: 119 ms · mais rápido: Neo4j, 1,5× mais rápido

Contrariou a expectativa. Provável causa: no SQL, o COUNT(DISTINCT) sobre a junção movie_genres × ratings obriga a ordenar mais de 266 mil linhas. No grafo, cada gênero só expande os próprios filmes. Com 20 milhões de notas, a varredura tende a voltar a favorecer o SQL.

## Consulta 4 · Filmes marcados com uma tag

*Quais filmes foram marcados com 'pixar' ou 'animation'?*

- PostgreSQL: 4,2 ms · Neo4j: 6,8 ms · mais rápido: PostgreSQL, 1,6× mais rápido

O mesmo caminho lógico nos dois bancos: achar a tag pelo índice (tags.tag_name no SQL, a constraint de :Tag no grafo) e seguir até os filmes. Com um único salto e índices dos dois lados, a diferença é de apenas 2,6 ms.

## Consulta 5 · Quem gostou também gostou

*Quem deu nota ≥ 4 a Toy Story também avaliou bem quais outros filmes?*

- PostgreSQL: 13 ms · Neo4j: 26 ms · mais rápido: PostgreSQL, 1,9× mais rápido

Com 2 saltos e os índices certos, o self-join de ratings é eficiente. A vantagem do Cypher aqui é de leitura: o padrão filme ← usuário → filme é o desenho da própria pergunta. Lidera Forrest Gump, com 83 usuários em comum.

## Consulta 6 · Similares por tags em comum

*Quais filmes compartilham mais tags com Toy Story?*

- PostgreSQL: 136 ms · Neo4j: 12 ms · mais rápido: Neo4j, 11,6× mais rápido

O SQL precisa deduplicar as 465 mil linhas de user_movie_tags antes do self-join. No grafo essa agregação foi feita uma vez, na carga (HAS_TAG {count}), e a consulta só caminha filme → tag → filme. Lidera Toy Story 2, com 34 tags em comum.

## Consulta 7 · Sugestão por gênero

*Que filmes se parecem com Toy Story em gêneros e, no empate, em tags?*

- PostgreSQL: 208 ms · Neo4j: 72 ms · mais rápido: Neo4j, 2,9× mais rápido

A pergunta cruza duas vizinhanças do mesmo filme: as tags e os gêneros. No Cypher são dois caminhos de 2 saltos a partir do mesmo nó (Movie→Tag→Movie e Movie→Genre→Movie), e o banco só visita os filmes realmente vizinhos de Toy Story. No SQL é preciso deduplicar user_movie_tags (465 mil linhas), fazer o self-join por tag e depois juntar movie_genres e agrupar de novo. É o mesmo princípio da Consulta 6, com uma segunda vizinhança em cima.
