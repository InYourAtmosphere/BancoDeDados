# Projeto de Banco de Dados: Análise Comparativa Relacional vs. NoSQL

Este repositório contém a implementação completa, scripts de ETL, modelagens e análise comparativa entre um **SGBD Relacional (PostgreSQL e SQLite normalizados até a 3FN)** e um **SGBD Não-Relacional (MongoDB orientado a documentos)**, utilizando a base de dados pública **MovieLens 20M**.

---

## 📁 Estrutura do Projeto

```text
ProjetoBancoDados/
├── data/                           # (não versionado) preenchido pelos scripts
│   ├── raw/                        # CSVs originais do MovieLens 20M (movies, ratings, tags, links, genome-*)
│   └── processed/                  # Documentos gerados em JSON Lines (movies.jsonl, ratings.jsonl)
│
├── relational/
│   ├── schema.sql                  # DDL ANSI SQL padronizado (compatível com SQLite e PostgreSQL)
│   ├── postgres_schema.sql         # DDL especializado para PostgreSQL com tipos e constraints nativas
│   ├── load_postgres.sql           # Script de carga ultrarrápida via staging e comando COPY
│   ├── queries.sql                 # Consultas analíticas SQL para validação e benchmark
│   └── movielens.db                # Banco de dados SQLite gerado e validado (3FN)
│
├── mongodb/
│   ├── import.py                   # Script de conexão, importação em lote e indexação no MongoDB
│   └── queries.js                  # Consultas analíticas equivalentes em MQL e Aggregation Pipeline
│
├── scripts/
│   ├── download_data.py            # Download e extração do MovieLens 20M a partir do GroupLens
│   ├── load_relational.py          # Script ETL Python para normalização 3FN e carga no banco relacional
│   ├── transform.py                # Script ETL Python para desnormalização e geração de JSON Lines
│   └── test_nosql_queries.py       # Validador autônomo das 4 consultas documentais
│
├── docs/
│   └── analise.md                  # Relatório técnico completo e aprofundado do Passo 3
│
├── docker-compose.yml              # Ambiente conteinerizado com PostgreSQL 16 e MongoDB 7.0
└── README.md                       # Documentação geral do repositório
```

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
* **Python 3.10+** com bibliotecas padrão (`sqlite3`) e pacotes:
  ```bash
  pip install pandas pymongo
  ```
* *(Opcional)* **Docker & Docker Compose** (para rodar os servidores oficiais de PostgreSQL e MongoDB).

---

### Passo 0: Obter os Dados

A base utilizada é o **[MovieLens 20M](https://grouplens.org/datasets/movielens/20m/)**, disponibilizada pelo GroupLens (Universidade de Minnesota). Por causa do tamanho (~190 MB compactados, com `ratings.csv` acima de 500 MB), os dados **não são versionados** no repositório.

Para baixar e extrair os CSVs em `data/raw/`:
```bash
python scripts/download_data.py
```
*(Se os arquivos já existirem, o download é pulado. Para baixar novamente, utilize a flag `--force`).*

Arquivos esperados em `data/raw/`:

| Arquivo | Conteúdo |
| :--- | :--- |
| `movies.csv` | Filmes (`movieId`, `title`, `genres`) |
| `ratings.csv` | Avaliações (`userId`, `movieId`, `rating`, `timestamp`) |
| `tags.csv` | Tags livres atribuídas por usuários |
| `links.csv` | Identificadores externos (IMDb e TMDb) |
| `genome-scores.csv` | Relevância de cada tag do genoma para cada filme |
| `genome-tags.csv` | Catálogo de tags do genoma |

> **Licença:** o MovieLens permite uso acadêmico, mas exige citação e proíbe a redistribuição dos dados. Por isso os CSVs não são incluídos neste repositório.
> F. Maxwell Harper and Joseph A. Konstan. 2015. *The MovieLens Datasets: History and Context.* ACM Transactions on Interactive Intelligent Systems (TiiS) 5, 4, Article 19. https://doi.org/10.1145/2827872

---

### Passo 1: Banco Relacional (Normalização e Carga)

1. **Executar a Carga Relacional no SQLite**:
   O script processa os CSVs em `data/raw/`, aplica a normalização até a **3FN** (atomizando gêneros, separando anos e catalogando tags unívocas) e popula o banco com integridade referencial:
   ```bash
   python scripts/load_relational.py --sample-ratings 100000
   ```
   *(Para carregar todos os 20 milhões de ratings, utilize a flag `--all-ratings`).*

2. **Testar as Consultas SQL de Benchmark**:
   ```bash
   python -c "
   import sqlite3, pandas as pd
   conn = sqlite3.connect('relational/movielens.db')
   with open('relational/queries.sql') as f:
       for i, q in enumerate(f.read().split(';')[:-1], 1):
           print(f'=== CONSULTA {i} ===\n', pd.read_sql_query(q, conn).head(3), '\n')
   "
   ```

3. *(Opcional)* **Executar no PostgreSQL via Docker**:
   ```bash
   docker compose up -d postgres
   docker exec -i movielens_postgres psql -U postgres -d movielens < relational/postgres_schema.sql
   ```

---

### Passo 2: Banco Não-Relacional (MongoDB)

1. **Transformar os Dados para o Formato Documental**:
   Gera os arquivos `movies.jsonl` e `ratings.jsonl` em `data/processed/`, aplicando *embedding* de gêneros, links e métricas pré-computadas:
   ```bash
   python scripts/transform.py --sample-ratings 100000
   ```

2. **Testar as Consultas Documentais (Modo Autônomo)**:
   Valida instantaneamente a equivalência das consultas sobre os documentos JSON gerados sem necessidade de servidor ativo:
   ```bash
   python scripts/test_nosql_queries.py
   ```

3. **Importar para o MongoDB (Servidor / Docker)**:
   ```bash
   docker compose up -d mongodb
   python mongodb/import.py
   ```

4. **Executar Consultas MQL via MongoDB Shell (`mongosh`)**:
   ```bash
   mongosh "mongodb://root:mongopassword@localhost:27017/movielens?authSource=admin" mongodb/queries.js
   ```

---

### Passo 3: Análise Comparativa e Resultados

O relatório técnico detalhado com fundamentação teórica, análise de redundâncias, confronto das consultas SQL vs. MQL, propriedades ACID vs. Teorema CAP e recomendações de arquitetura está disponível na íntegra em:

📄 **[Relatório Técnico de Análise Comparativa (docs/analise.md)](docs/analise.md)**

---

## 📊 Síntese dos Resultados Obtidos

| Dimensão | Modelo Relacional (3FN) | Modelo Não-Relacional (MongoDB) |
| :--- | :--- | :--- |
| **Organização** | 8 tabelas normalizadas | 2 coleções (`movies` e `ratings`) |
| **Gêneros** | Tabela associativa $N:M$ (`movie_genres`) | Array embutido com índice *Multikey* |
| **Links Externos** | Tabela 1:1 separada (`movie_links`) | Subdocumento embutido (`links`) |
| **Tags de Usuários**| Catálogo único `tags` + `user_movie_tags` | Array de termos únicos no documento |
| **Avaliações** | Tabela normalizada com PK composta | Coleção referenciada (evita estouro de 16MB) |
| **Consulta de Ficha**| 4 `JOIN`s com `GROUP BY` e `COUNT/AVG` | Busca pontual direta $O(1)$ por `_id` |
| **Integridade** | Chaves estrangeiras estritas no SGBD | Delegada à camada de aplicação |
| **Consistência** | ACID estrito e transacional | BASE / Consistência Eventual |
