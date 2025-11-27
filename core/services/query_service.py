# core/services/query_service.py

import json
import os
from typing import Dict, Any, Optional, List

from mistralai import Mistral

from core.storage.postgres_client import execute
from services.api.app import rag  # your existing rag search
from services.api.app.schemas.ask import AskResponse, Citation


MISTRAL_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

client = Mistral(api_key=MISTRAL_KEY)


# --------------------------
# 1. Identify SQL questions
# --------------------------
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

There are two tables:

uploaded_files(id UUID, filename TEXT)
extracted_rows(id SERIAL, file_id UUID, table_name TEXT, row_data JSONB)

All actual columns live inside row_data:
Example: row_data->>'Department', row_data->>'Year', row_data->>'Name'

RULES:
- If user asks "how many" → use COUNT(*)
- For listing → SELECT row_data
- Use ILIKE for matching text
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

    content = resp.choices[0].message.content.strip()

    try:
        obj = json.loads(content)
        return obj.get("sql")
    except:
        return None


# --------------------------
# 2. Execute SQL
# --------------------------
def answer_with_sql(question: str) -> Optional[AskResponse]:
    sql = generate_sql(question)
    if sql is None:
        return None

    rows = execute(sql)

    # COUNT(*)
    if len(rows) == 1 and len(rows[0]) == 1:
        val = list(rows[0].values())[0]
        return AskResponse(answer=f"The result is: {val}", citations=[])

    # list rows
    lines = []
    for r in rows[:10]:
        lines.append(str(r))

    txt = "\n".join(lines)
    return AskResponse(answer=f"Here are some results:\n{txt}", citations=[])


# --------------------------
# 3. Fallback to RAG
# --------------------------
def answer_with_rag(question: str, top_k: int) -> AskResponse:
    hits = rag.search(question, top_k)

    context = []
    for h in hits:
        context.append(f"[doc:{h['doc_id']}] {h['text']}")
    context_str = "\n".join(context)

    rag_prompt = f"""
Answer using ONLY this context. If insufficient, say "I don't know."

Question: {question}
Context:
{context_str}
"""

    resp = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[
            {"role": "user", "content": rag_prompt}
        ],
        temperature=0.1,
    )

    ans = resp.choices[0].message.content.strip()

    citations = [
        Citation(
            doc_id=str(h["doc_id"]),
            chunk=h["chunk_id"],
            score=h["score"],
            text=h["text"],
        )
        for h in hits
    ]

    return AskResponse(answer=ans, citations=citations)


# --------------------------
# 4. Public entry for ask.py
# --------------------------
def answer_query(query: str, top_k: int, user_id=None) -> Dict[str, Any]:
    sql_answer = answer_with_sql(query)
    if sql_answer:
        return sql_answer.dict()

    rag_answer = answer_with_rag(query, top_k)
    return rag_answer.dict()
