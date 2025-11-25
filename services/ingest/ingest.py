import os
import time
import requests
from pathlib import Path
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer


# -------------------------------
# Environment variables
# -------------------------------
INDEX_NAME  = os.getenv("INDEX_NAME", "docs")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DATA_DIR    = Path(os.getenv("DATA_DIR", "/workspace/data"))


# -------------------------------
# Qdrant readiness
# -------------------------------
def wait_for_qdrant(url="http://qdrant:6333/readyz"):
    print("⏳ Waiting for Qdrant to be ready...")

    for _ in range(40):
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                print("✅ Qdrant is ready.")
                return
        except:
            pass
        time.sleep(2)

    raise RuntimeError("❌ Qdrant did not become ready in time!")


# -------------------------------
# Clean & extract Excel content
# -------------------------------
def read_excel(path: Path):
    print(f"📥 Reading Excel: {path.name}")

    df = pd.read_excel(path, dtype=str)
    df = df.fillna("")

    chunks = []

    for _, row in df.iterrows():
        row_text = " | ".join(
            [cell.strip() for cell in row.values if cell.strip() != ""]
        )
        if len(row_text) > 10:
            chunks.append(row_text)

    print(f"➡ Extracted {len(chunks)} cleaned rows from {path.name}")
    return chunks


# -------------------------------
# Clean & extract CSV content
# -------------------------------
def read_csv(path: Path):
    print(f"📥 Reading CSV: {path.name}")

    df = pd.read_csv(path, dtype=str)
    df = df.fillna("")

    chunks = []

    for _, row in df.iterrows():
        row_text = " | ".join(
            [cell.strip() for cell in row.values if cell.strip() != ""]
        )
        if len(row_text) > 10:
            chunks.append(row_text)

    print(f"➡ Extracted {len(chunks)} cleaned rows from {path.name}")
    return chunks


# -------------------------------
# Generic file loader
# -------------------------------
def read_file(path: Path):
    if path.suffix.lower() == ".xlsx":
        return read_excel(path)
    if path.suffix.lower() == ".csv":
        return read_csv(path)
    if path.suffix.lower() == ".txt":
        return [path.read_text()]

    print(f"⚠ Unsupported file type: {path.name}")
    return []


# -------------------------------
# Ingest everything
# -------------------------------
def ingest_all():
    print(f"📁 Scanning directory: {DATA_DIR.resolve()}")

    model = SentenceTransformer(EMBED_MODEL)
    qdrant = QdrantClient(QDRANT_HOST, port=6333)

    # Create collection if missing
    if not qdrant.collection_exists(INDEX_NAME):
        print(f"🆕 Creating Qdrant collection '{INDEX_NAME}' ...")
        qdrant.create_collection(
            collection_name=INDEX_NAME,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        )

    global_id = 1

    for file in DATA_DIR.iterdir():
        print(f"\n📄 Processing file: {file.name}")
        chunks = read_file(file)

        if not chunks:
            print("⚠ No usable chunks in this file.")
            continue

        vectors = model.encode(chunks, show_progress_bar=True).tolist()

        payloads = [
            {"text": text, "filename": file.name}
            for text in chunks
        ]

        ids = list(range(global_id, global_id + len(vectors)))
        global_id += len(vectors)

        print(f"➡ Uploading {len(vectors)} vectors ...")

        qdrant.upsert(
            collection_name=INDEX_NAME,
            points=models.Batch(
                ids=ids,
                vectors=vectors,
                payloads=payloads
            )
        )

        print(f"✅ Completed ingestion for {file.name}")


# -------------------------------
# Entrypoint
# -------------------------------
if __name__ == "__main__":
    wait_for_qdrant()
    ingest_all()
    print("\n🎉 Ingestion complete!")
