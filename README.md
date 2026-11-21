# Projeto de Banco de Dados: Análise Comparativa Relacional vs. Grafo

Este repositório contém a implementação, os scripts de ETL, as modelagens e a análise comparativa entre um **SGBD Relacional (PostgreSQL normalizado até a 3FN)** e um **SGBD NoSQL orientado a Grafos (Neo4j)**, usando a base pública **MovieLens 20M**.

O MovieLens é, essencialmente, uma rede: usuários ligados a filmes pelas avaliações, filmes ligados a gêneros e tags. O trabalho compara os dois modelos em consultas típicas de catálogo (em que o relacional é forte) e em consultas de recomendação e caminhos (em que o grafo é forte), com tempos medidos.

---

## 📁 Estrutura do Projeto

```text
BancoDeDados/
├── data/raw/                       # CSVs do MovieLens (baixados por scripts/download_data.py)
├── relational/
│   ├── postgres_ddl.sql            # DDL do PostgreSQL (3FN, constraints e índices)
│   ├── clean.sql                   # Remove todas as tabelas (para recriar o esquema do zero)
│   └── queries.sql                 # As 7 consultas de comparação em SQL
├── neo4j/
│   ├── schema.cypher               # Constraints de unicidade e índices do grafo
│   └── queries.cypher              # As 7 consultas equivalentes em Cypher
├── scripts/
│   ├── download_data.py            # Baixa e extrai o MovieLens 20M
│   ├── load_relational.py          # ETL: CSVs -> PostgreSQL normalizado (COPY)
│   ├── load_neo4j.py               # ETL: CSVs -> grafo no Neo4j (UNWIND em lotes)
│   ├── test_sql_queries.py         # Executa e exibe as consultas SQL
│   ├── test_graph_queries.py       # Executa e exibe as consultas Cypher
│   ├── benchmark.py                # Mede o tempo das consultas nos dois bancos
│   └── common.py                   # Conexões e funções compartilhadas
├── docs/
│   ├── analise.md                  # Relatório técnico completo
│   ├── resultados_benchmark.md     # Gerado por scripts/benchmark.py
│   ├── der.drawio                  # Diagrama entidade-relacionamento
│   └── modelo_logico.puml          # Modelo lógico relacional (PlantUML)
├── docker-compose.yml              # PostgreSQL 16 e Neo4j 5.26
├── requirements.txt
└── executar_tudo.sh / .bat         # Executa tudo de uma vez (Linux/macOS e Windows)
```

---

## 🚀 Como Executar

### Pré-requisitos

* **Docker** e **Docker Compose**.
* **Python 3.10+**:
  ```bash
  pip install -r requirements.txt
  ```

### Execução automática

```bash
./executar_tudo.sh        # Linux/macOS
executar_tudo.bat         # Windows
```

O script sobe os containers, baixa os dados, carrega os dois bancos, executa as consultas e roda o benchmark.

### Execução passo a passo

```bash
docker compose up -d                 # PostgreSQL (5432) e Neo4j (7474 / 7687)
python scripts/download_data.py      # dados em data/raw/

# Relacional
python scripts/load_relational.py --sample-ratings 100000
python scripts/test_sql_queries.py

# Grafo
python scripts/load_neo4j.py --sample-ratings 100000
python scripts/test_graph_queries.py

# Tempos (gera docs/resultados_benchmark.md)
python scripts/benchmark.py
```

Para carregar os 20 milhões de avaliações, use `--all-ratings` nos dois scripts de carga. No Neo4j a carga completa via Cypher é demorada; a amostra de 100 mil é suficiente para a comparação.

As consultas também podem ser executadas direto nos clientes de cada banco:

```bash
psql -h localhost -U postgres -d movielens -f relational/queries.sql
cypher-shell -a bolt://localhost:7687 -u neo4j -p neo4jpassword -f neo4j/queries.cypher
```

O **Neo4j Browser** (http://localhost:7474, usuário `neo4j`, senha `neo4jpassword`) mostra os resultados como grafo, o que é ótimo para a apresentação. Experimente:

```cypher
MATCH p = (:Movie {movie_id: 1})-[:HAS_TAG]->(:Tag)<-[:HAS_TAG]-(:Movie) RETURN p LIMIT 30
```

---

## 🔎 As 7 consultas comparadas

| # | Consulta | Favorece |
| :--- | :--- | :--- |
| 1 | Ficha completa de um filme | — (busca pontual) |
| 2 | Top 10 filmes (mínimo de 50 votos) | Relacional (agregação global) |
| 3 | Filmes e média por gênero | Relacional (agregação global) |
| 4 | Filmes com as tags `pixar` / `animation` | — |
| 5 | "Quem gostou deste também gostou de..." | Grafo (legibilidade) |
| 6 | Filmes com mais tags em comum | Grafo (vizinhança) |
| 7 | Sugestão por gênero (desempate por tags) | **Grafo** (vizinhanças cruzadas) |

---

## 📊 Síntese

| Dimensão | Relacional (PostgreSQL / 3FN) | Grafo (Neo4j) |
| :--- | :--- | :--- |
| **Organização** | 8 tabelas normalizadas | 4 tipos de nó e 3 tipos de aresta |
| **Gêneros** | Tabela associativa $N:M$ (`movie_genres`) | Aresta `IN_GENRE` para nós `:Genre` |
| **Links externos** | Tabela 1:1 (`movie_links`) | Propriedades do nó `:Movie` |
| **Avaliações** | Tabela com PK composta | Aresta `RATED {rating, rated_at}` |
| **Tags** | Catálogo `tags` + `user_movie_tags` | Aresta `HAS_TAG {count}` para nós `:Tag` |
| **Relacionamentos** | Calculados na consulta (`JOIN`) | Armazenados como ponteiros |
| **Integridade** | FK, `CHECK`, tipos | Unicidade; arestas nunca órfãs |
| **Transações** | ACID | ACID |

📄 Relatório completo: **[docs/analise.md](docs/analise.md)**
