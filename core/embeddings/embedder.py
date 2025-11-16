from typing import List
from .model_loader import get_embedding_model

def embed_text(text: str, normalize: bool = True) -> List[float]:
    """
    Embed a single text into a vector.
    """
    model = get_embedding_model()
    vec = model.encode([text], normalize_embeddings=normalize)[0]
    return vec.tolist()

def embed_texts(texts: List[str], normalize: bool = True) -> List[List[float]]:
    """
    Embed a list of texts into vectors.
    """
    model = get_embedding_model()
    vecs = model.encode(texts, normalize_embeddings=normalize)
    return [v.tolist() for v in vecs]

