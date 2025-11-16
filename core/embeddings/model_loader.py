from functools import lru_cache
import os
from sentence_transformers import SentenceTransformer

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Loads the embedding model once and caches it.
    """
    print(f"📥 Loading embedding model: {EMBED_MODEL}")
    return SentenceTransformer(EMBED_MODEL)

