# Projeto de Banco de Dados: Análise Comparativa Relacional vs. NoSQL

Este repositório contém a implementação completa, scripts de ETL, modelagens e análise comparativa entre um **SGBD Relacional (PostgreSQL normalizado até a 3FN)** e um **SGBD Não-Relacional (MongoDB orientado a documentos)**, utilizando a base de dados pública **MovieLens 20M**.

---

## 📁 Estrutura do Projeto

```text
ProjetoBancoDados/
├── data/
│   ├── raw/                        # CSVs originais do MovieLens (movie, rating, tag, link, genome)
│
├── relational/
│   ├── postgres_ddl.sql            # DDL do PostgreSQL com tipos e constraints nativas
│   ├── queries.sql                 # Consultas analíticas SQL para validação e benchmark
│
├── mongodb/
│   └── queries.js                  # Consultas analíticas equivalentes em MQL e Aggregation Pipeline
│
├── scripts/
│   ├── load_relational.py          # Script ETL Python para normalização 3FN e carga no banco relacional
│   ├── load_mongo.py               # Script ETL Python: CSVs brutos -> documentos -> MongoDB (bulk + índices)
│   ├── test_sql_queries.py         # Executa as 4 consultas no PostgreSQL
│   └── test_nosql_queries.py       # Executa as 4 consultas equivalentes no MongoDB
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
* **Python 3.10+** e pacotes:
  ```bash
  pip install pandas pymongo psycopg2-binary
  ```
* **Docker & Docker Compose** (servidores oficiais de PostgreSQL e MongoDB).

---

### Passo 1: Banco Relacional (Normalização e Carga)

1. **Subir o PostgreSQL e executar a Carga Relacional**:
   O script processa os CSVs em `data/raw/`, aplica a normalização até a **3FN** (atomizando gêneros, separando anos e catalogando tags unívocas) e popula o banco com integridade referencial:
   ```bash
   docker compose up -d postgres
   python scripts/load_relational.py --sample-ratings 100000
   ```
   *(Para carregar todos os 20 milhões de ratings, utilize a flag `--all-ratings`).*

2. **Testar as Consultas SQL de Benchmark**:
   ```bash
   python scripts/test_sql_queries.py
   ```

---

### Passo 2: Banco Não-Relacional (MongoDB)

1. **Subir o MongoDB e carregar os dados**:
   Lê os CSVs de `data/raw/`, monta os documentos (*embedding* de gêneros, links, tags e métricas pré-computadas), insere em `movies` e `ratings` e cria os índices:
   ```bash
   docker compose up -d mongodb
   python scripts/load_mongo.py --sample-ratings 100000
   ```
   *(Para carregar todos os 20 milhões de ratings, utilize a flag `--all-ratings`).*

2. **Testar as Consultas Documentais**:
   ```bash
   python scripts/test_nosql_queries.py
   ```

3. **Executar Consultas MQL via MongoDB Shell (`mongosh`)**:
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
