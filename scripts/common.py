import re

_TITLE_YEAR = re.compile(r"^(.*?)\s*\((\d{4})\)\s*$")


def extract_title_and_year(raw_title):
    """1FN: 'Toy Story (1995)' -> ('Toy Story', 1995). Sem ano -> (título, None)."""
    if not isinstance(raw_title, str):
        return str(raw_title), None
    raw_title = raw_title.strip()
    m = _TITLE_YEAR.match(raw_title)
    return (m.group(1).strip(), int(m.group(2))) if m else (raw_title, None)


def connect(host="localhost", port=5432, db="movielens", user="postgres", password=None):
    """Conexão PostgreSQL com os defaults do docker-compose.yml."""
    import os
    import psycopg2
    return psycopg2.connect(host=host, port=port, dbname=db, user=user,
                            password=password or os.environ.get("PGPASSWORD", "postgrespassword"))


MONGO_URI = "mongodb://root:mongopassword@localhost:27017/?authSource=admin"  # docker-compose.yml
