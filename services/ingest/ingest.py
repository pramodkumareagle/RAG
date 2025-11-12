import os, glob, uuid, io
from typing import Iterable, Tuple
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import chardet
import pandas as pd

INDEX_NAME = os.getenv("INDEX_NAME", "docs")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DATA_DIR = os.getenv("DATA_DIR", "./data")

client = QdrantClient(host=QDRANT_HOST)
model = SentenceTransformer(EMBED_MODEL)

client.recreate_collection(
    collection_name=INDEX_NAME,
    vectors_config=qmodels.VectorParams(
        size=384,
        distance=qmodels.Distance.COSINE
    )
)

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> Iterable[str]:
    text = " ".join(text.split()) # normalize whitespace
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        yield text[start:end]
        if end == len(text):
            break
        start = end - overlap

def read_txt(path: str) -> str:
    with open(path, 'rb', encoding="utf-8", errors="ignore") as f:
        return f.read()
    

def read_pdf(path: str) -> str:
    out = []
    reader = PdfReader(path)
    for page in reader.pages:
        out.append(page.extract_text())
    return "\n".join(out)


def read_csv(path: str, max_rows: int = 5000) -> str:
    with open(path, 'rb') as f:
        raw = f.read(4096)
    enc = chardet.detect(raw).get('encoding') or 'utf-8'
    df = pd.read_csv(path, encoding=enc)
    if len(df) > max_rows:
        df = df.head(max_rows)

    lines = [f"CSV File: {os.path.basename(path)}; columns: {', '.join(df.columns)}; rows: {len(df)}"]
    sample = df.astype(str).head(50)
    for i, row in sample.iterrows():
        lines = "; ".join([f"{col}={row[col]}" for col in df.columns])
        lines.append(lines)
    return "\n".join(lines)
