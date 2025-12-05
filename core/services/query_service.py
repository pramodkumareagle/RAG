# core/services/query_service.py

import json
import os
from typing import Dict, Any, Optional, List

from mistralai import Mistral
from core.storage.postgres_client import execute
from services.api.app.schemas.ask import AskResponse, Citation

# -----------------------------
# Mistral configuration
# -----------------------------
MISTRAL_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

client = Mistral(api_key=MISTRAL_KEY)


# -----------------------------
# 1. Identify SQL questions
# -----------------------------
def is_sql_question(q: str) -> bool:
    q = q.lower()
    return any(
        kw in q
        for kw in [
            "how many",
            "number of",
            "count",
            "list",
            "show",
            "find all",
            "give me all",
        ]
    )


SQL_PROMPT = """
You are a SQL generator for PostgreSQL.

Tables:
uploaded_files(id UUID, filename TEXT)
extracted_rows(id SERIAL, file_id UUID, table_name TEXT, row_data JSONB)

All real columns live inside row_data:
Example: row_data->>'Department'

RULES:
- Use COUNT(*) for "how many"
- Use SELECT row_data for listings
- Use ILIKE for text filtering
- Always output valid JSON only:
{ "sql": "SELECT ...;" }
"""


def generate_sql(question: str) -> Optional[str]:
    if not is_sql_question(question):
        return None

    messages = [
        {"role": "system", "content": SQL_PROMPT},
        {"role": "user", "content": question},
    ]

    resp = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=messages,
        temperature=0,
    )

    # NEW MISTRAL SDK RETURNS .content
    content = resp.choices[0].message.content.strip()

    try:
        obj = json.loads(content)
        return obj.get("sql")
    except Exception:
        return None


# -----------------------------
# 2. Execute SQL
# -----------------------------
def answer_with_sql(question: str) -> Optional[AskResponse]:
    sql = generate_sql(question)
    if sql is None:
        return None

    rows = execute(sql)

    # COUNT(*) case
    if len(rows) == 1 and len(rows[0]) == 1:
        value = list(rows[0].values())[0]
        return AskResponse(answer=f"The result is: {value}", citations=[])

    # list rows
    lines = [str(r) for r in rows[:10]]
    return AskResponse(answer="\n".join(lines), citations=[])


# -----------------------------
# 3. Postgres RAG (no Qdrant)
# -----------------------------
def answer_with_rag(question: str, top_k: int) -> AskResponse:
    db_rows = execute(
        """
        SELECT text
        FROM extracted_text
        ORDER BY created_at DESC
        LIMIT %s;
        """,
        (top_k,),
    )

    docs = [r["text"] for r in db_rows if r["text"]]

    context_block = "\n\n".join(docs) if docs else "No documents found."

    prompt = f"""
Answer the question using ONLY the context below. 
If you cannot answer from the context, reply: "I don't know."

Question: {question}

Context:
{context_block}
"""

    resp = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    # FIXED: USE .content
    answer = resp.choices[0].message.content.strip()

    citations = [
        Citation(doc_id=str(i), chunk=0, score=1.0, text=text)
        for i, text in enumerate(docs)
    ]

    return AskResponse(answer=answer, citations=citations)


# -----------------------------
# 4. Entry point
# -----------------------------
def answer_query(query: str, top_k: int = 5, user_id=None) -> Dict[str, Any]:
    sql_result = answer_with_sql(query)
    if sql_result:
        return sql_result.dict()

    rag_result = answer_with_rag(query, top_k)
    return rag_result.dict()
