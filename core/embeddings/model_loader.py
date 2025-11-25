import os
from sentence_transformers import SentenceTransformer

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Global cached model instance
_model = None


def get_embedding_model():
    """
    Loads and caches the embedding model on CPU.

    Using device='cpu' avoids the PyTorch 'meta tensor' bug inside Docker
    (caused by missing GPU / incompatible torch build).
    """
    global _model

    if _model is None:
        print(f"🔵 Loading embedding model: {EMBED_MODEL}")
        _model = SentenceTransformer(EMBED_MODEL, device="cpu")   # FIXED: force CPU

    return _model
