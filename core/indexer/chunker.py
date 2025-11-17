def chunk_text(text: str, max_chars: int = 900, overlap: int = 120):
    """
    Splits text into overlapping chunks suitable for embeddings.
    """
    text = " ".join(text.split())  # Normalize whitespace
    start = 0
    n = len(text)

    while start < n:
        end = min(start + max_chars, n)
        yield text[start:end]

        if end == n:
            break

        start = end - overlap

