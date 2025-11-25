import json
from typing import List, Dict, Any, Optional

from core.retrievers.semantic_retriever import semantic_search
from core.storage.postgres_client import execute as pg_execute
from core.llm.hf_client import generate_llm_answer
from core.llm.llm_client import generate_answer


def log_query(user_id: Optional[str], query: str, results: List[Dict[str, Any]]):
    try:
        top_docs = [
            {
                "filename": r.get("source"),
                "score": r.get("score"),
                "doc_id": r.get("id"),
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


def answer_query(query: str, top_k: int = 5, user_id: Optional[str] = None):

    # Semantic search
    results = semantic_search(query, top_k=top_k)
    if results is None:
        results = []

    # Generate final answer
    answer_text = generate_answer(query, results)

    # Always return valid structure
    return {
        "answer": answer_text,
        "results": results
    }