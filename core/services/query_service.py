import json
from typing import List, Dict, Any, Optional

from core.retrievers.semantic_retriever import semantic_search
from core.storage.postgres_client import execute as pg_execute


def build_answer(query: str, results: List[Dict[str, Any]]) -> str:
    """
    Build a human-readable answer summarizing the retrieved chunks.
    """

    if not results:
        return f"I couldn't find any relevant information for: '{query}'."

    lines = [f"### Found {len(results)} relevant pieces:"]
    lines.append("")

    for i, r in enumerate(results, start=1):
        source = r.get("filename") or r.get("source_path") or "Unknown Source"
        score = r["score"]

        lines.append(f"**{i}. From:** `{source}` (score={score:.4f})")
        lines.append(r["text"])
        lines.append("")

    return "\n".join(lines)


def log_query(user_id: Optional[str], query: str, results: List[Dict[str, Any]]):
    """
    Log the query analytics into Postgres.
    Safe: failure will not break main flow.
    """
    try:
        top_docs = [
            {
                "filename": r.get("filename"),
                "score": r.get("score"),
                "doc_id": r.get("doc_id"),
            }
            for r in results
        ]

        pg_execute(
            """
            INSERT INTO queries (user_id, query, top_docs)
            VALUES (%s, %s, %s)
            """,
            (user_id, query, json.dumps(top_docs)),
        )
    except Exception as e:
        print("[WARN] Failed to log query:", e)


def answer_query(
    query: str,
    top_k: int = 5,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    High-level pipeline:

    1. Retrieve
    2. Build final answer text
    3. Log analytics
    4. Return structured result

    This is what the FastAPI /ask endpoint calls.
    """

    # Step 1 — Retrieve relevant chunks
    results = semantic_search(query, top_k=top_k)

    # Step 2 — Build user-friendly answer
    answer_text = build_answer(query, results)

    # Step 3 — Log analytics
    log_query(user_id or "anonymous", query, results)

    # Step 4 — Return structured payload
    return {
        "answer": answer_text,
        "results": results,
    }

