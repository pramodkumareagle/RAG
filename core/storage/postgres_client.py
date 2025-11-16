import os
from functools import lru_cache
from typing import Optional, List, Any

import psycopg2
from psycopg2.extras import RealDictCursor

PG_DSN = os.getenv("PG_DSN")


@lru_cache(maxsize=1)
def get_pg_conn():
    """
    Returns a cached Postgres connection.
    If PG_DSN is missing, ingestion/logging will be disabled gracefully.
    """
    if not PG_DSN:
        raise RuntimeError("PG_DSN environment variable not set.")
    
    conn = psycopg2.connect(PG_DSN)
    conn.autocommit = True
    return conn


def execute(query: str, params: Optional[tuple] = None) -> List[Any]:
    """
    Execute SELECT/INSERT/UPDATE queries.
    Always returns a list (may be empty).
    """
    conn = get_pg_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params or ())
        try:
            return cur.fetchall()
        except psycopg2.ProgrammingError:
            # No results (e.g., INSERT)
            return []


def init_basic_schema():
    """
    Create the 2 main tables if they don't exist:
    - ingested_documents
    - queries (analytics)
    """

    docs_table = """
    CREATE TABLE IF NOT EXISTS ingested_documents (
        id SERIAL PRIMARY KEY,
        doc_id UUID NOT NULL,
        filename TEXT NOT NULL,
        source_path TEXT NOT NULL,
        num_chunks INT NOT NULL,
        status TEXT NOT NULL,
        error TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    );
    """

    queries_table = """
    CREATE TABLE IF NOT EXISTS queries (
        id SERIAL PRIMARY KEY,
        user_id TEXT,
        query TEXT NOT NULL,
        top_docs JSONB,
        created_at TIMESTAMPTZ DEFAULT now()
    );
    """

    execute(docs_table)
    execute(queries_table)

