# core/storage/postgres_client.py

import os
from functools import lru_cache
from typing import Optional, List, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.encoders import jsonable_encoder

PG_DSN = os.getenv("PG_DSN")


# -------------------------------------------------------
# CONNECTION
# -------------------------------------------------------
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
            return jsonable_encoder(cur.fetchall())
        except psycopg2.ProgrammingError:
            return []


# -------------------------------------------------------
# 1️⃣ USERS (AUTH)
# -------------------------------------------------------
def init_user_schema():
    execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)


# -------------------------------------------------------
# 2️⃣ FILE INGEST (USER OWNED)
# -------------------------------------------------------
def init_table_schema():
    """
    Base ingest tables
    """
    execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id UUID PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            filename TEXT NOT NULL,
            content_type TEXT,
            storage_path TEXT,
            doc_type TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS extracted_rows (
            id SERIAL PRIMARY KEY,
            file_id UUID REFERENCES uploaded_files(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            table_name TEXT,
            row_data JSONB,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS extracted_text (
            id SERIAL PRIMARY KEY,
            file_id UUID REFERENCES uploaded_files(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            text TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)


# -------------------------------------------------------
# 3️⃣ RAG / QUERY METADATA
# -------------------------------------------------------
def init_basic_schema():
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
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            query TEXT NOT NULL,
            top_docs JSONB,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)


# -------------------------------------------------------
# 4️⃣ CHAT HISTORY (USER + DATE BASED)
# -------------------------------------------------------
def init_chat_schema():
    """
    Chat sessions + messages
    Supports:
    - global RAG chat
    - per-file chat
    - GitHub code chat
    """

    # -----------------------------
    # Chat sessions
    # -----------------------------
    execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id UUID PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            chat_type TEXT NOT NULL,            -- rag | file | code
            session_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)

    # -----------------------------
    # ADD file_id column (SAFE)
    # -----------------------------
    execute("""
        ALTER TABLE chat_sessions
        ADD COLUMN IF NOT EXISTS file_id UUID;
    """)

    # -----------------------------
    # ADD foreign key ONLY if missing
    # -----------------------------
    execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'chat_sessions_file_id_fkey'
            ) THEN
                ALTER TABLE chat_sessions
                ADD CONSTRAINT chat_sessions_file_id_fkey
                FOREIGN KEY (file_id)
                REFERENCES uploaded_files(id)
                ON DELETE CASCADE;
            END IF;
        END $$;
    """)

    # -----------------------------
    # Chat messages
    # -----------------------------
    execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id SERIAL PRIMARY KEY,
            session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            role TEXT CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            source JSONB,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)

    # -----------------------------
    # Index
    # -----------------------------
    execute("""
        CREATE INDEX IF NOT EXISTS idx_chat_user_type_file
        ON chat_sessions (user_id, chat_type, file_id);
    """)


# -------------------------------------------------------
# 5️⃣ CODE CHAT CACHE (KEEP)
# -------------------------------------------------------
def init_code_cache_schema():
    execute("""
        CREATE TABLE IF NOT EXISTS code_chat_cache (
            id SERIAL PRIMARY KEY,
            question TEXT NOT NULL,
            language TEXT,
            repo TEXT,
            answer TEXT NOT NULL,
            source JSONB,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)


# -------------------------------------------------------
# 🚀 MASTER INIT (CALL THIS)
# -------------------------------------------------------
def init_all_schemas():
    """
    SAFE ORDERED INITIALIZATION
    """
    init_user_schema()
    init_table_schema()
    init_basic_schema()
    init_chat_schema()
    init_code_cache_schema()
