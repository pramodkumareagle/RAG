from typing import List, Dict, Any
from core.embeddings.embedder import embed_text
from core.storage.qdrant_client import search_vectors


def semantic_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Run semantic vector search for the query against Qdrant.
    Returns a list of results with metadata.
    """

    # Convert query to embedding
    query_vec = embed_text(query)

    # Search Qdrant
    hits = search_vectors(query_vec, limit=top_k)

    results = []
    for h in hits:
        payload = h["payload"] or {}

        results.append({
            "score": h["score"],
            "text": payload.get("text", ""),
            "filename": payload.get("filename"),
            "source_path": payload.get("source_path"),
            "chunk": payload.get("chunk", 0),
            "doc_id": payload.get("doc_id")
        })

    return results

