# core/storage/postgres_client.py

import os
from functools import lru_cache
from typing import Optional, List, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.encoders import jsonable_encoder

PG_DSN = os.getenv("PG_DSN")


@lru_cache(maxsize=1)
def get_pg_conn():
    if not PG_DSN:
        raise RuntimeError("PG_DSN not set")
    conn = psycopg2.connect(PG_DSN)
    conn.autocommit = True
    return conn


def execute(query: str, params: Optional[tuple] = None) -> List[Any]:
    conn = get_pg_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params or ())
        try:
            rows = cur.fetchall()
            # ⭐ automatically make DB datetimes JSON-serializable
            return jsonable_encoder(rows)
        except psycopg2.ProgrammingError:
            return []


def init_basic_schema():
    """
    Original your 2 tables: ingested_documents & queries
    """
    execute("""
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
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id SERIAL PRIMARY KEY,
            user_id TEXT,
            query TEXT NOT NULL,
            top_docs JSONB,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)


def init_table_schema():
    """
    New tables used for generic file ingest & SQL chat.
    """
    execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id UUID PRIMARY KEY,
            filename TEXT NOT NULL,
            content_type TEXT,
            storage_path TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS extracted_rows (
            id SERIAL PRIMARY KEY,
            file_id UUID REFERENCES uploaded_files(id) ON DELETE CASCADE,
            table_name TEXT,
            row_data JSONB,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)
