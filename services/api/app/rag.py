import os
import numpy as np
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer

INDEX_NAME = os.getenv("QDRANT_INDEX_NAME", "doc")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBED_MODEL = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")

model = SentenceTransformer(EMBED_MODEL)
client = QdrantClient(url=QDRANT_URL)

def ensure_collection(dim: int = 384):
    try:
        client.get_collection(INDEX_NAME)
    except Exception:
        client.recreate_collection(
            collection_name=INDEX_NAME,
            vectors_config=qmodels.VectorParams(
                size=dim,
                distance=qmodels.Distance.COSINE
            )
        )

def embed(texts: List[str]) -> List[List[float]]:
    embed = model.encode(texts, convert_to_numpy=True).tolist()
    return embed


def search(query: str, top_k: int = 6) -> List[Dict]:
    query_vector = embed([query])[0]
    results = client.search(
        collection_name=INDEX_NAME,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True
    )
    formatted_results = []
    for res in results:
        formatted_results.append({
            "doc_id": res.id,
            "chunk_id": res.payload.get("chunk_id"),
            "text": res.payload.get("text"),
            "score": res.score,
            "payload": res.payload
        })
    return formatted_results