import os
from functools import lru_cache
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
INDEX_NAME = os.getenv("INDEX_NAME", "docs")
VECTOR_SIZE = 384  # MiniLM-L6-v2 uses 384 dims


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    """
    Returns a cached Qdrant client instance.
    """
    return QdrantClient(url=QDRANT_URL)


def ensure_collection():
    """
    Create Qdrant collection if it does not exist.
    Safe to call on every query.
    """
    client = get_qdrant_client()

    if not client.collection_exists(INDEX_NAME):
        client.create_collection(
            collection_name=INDEX_NAME,
            vectors_config=qm.VectorParams(
                size=VECTOR_SIZE,
                distance=qm.Distance.COSINE
            ),
        )


def search_vectors(query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search the vector DB and return structured results.
    """
    client = get_qdrant_client()
    ensure_collection()

    results = client.search(
        collection_name=INDEX_NAME,
        query_vector=query_vector,
        limit=limit,
        with_payload=True,
    )

    output = []
    for r in results:
        output.append({
            "id": r.id,
            "score": float(r.score),
            "payload": r.payload or {},
        })

    return output


def upsert_points(points: List[qm.PointStruct]):
    """
    Insert or update vector points.
    """
    if not points:
        return

    client = get_qdrant_client()
    ensure_collection()
    client.upsert(collection_name=INDEX_NAME, points=points)

