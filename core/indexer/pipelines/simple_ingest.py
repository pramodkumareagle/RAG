import os
import uuid
from qdrant_client.http import models as qm

from core.indexer.transformers.text_reader import read_text_file
from core.indexer.transformers.pdf_reader import read_pdf_file
from core.indexer.transformers.csv_reader import read_csv_file
from core.indexer.chunker import chunk_text
from core.embeddings.embedder import embed_texts
from core.storage.qdrant_client import upsert_points
from core.storage.postgres_client import execute as pg_execute


SUPPORTED_EXTS = {".txt", ".md", ".pdf", ".csv"}


def discover_files(base_dir: str):
    paths = []
    for root, _, files in os.walk(base_dir):
        for name in files:
            ext = os.path.splitext(name.lower())[1]
            if ext in SUPPORTED_EXTS:
                paths.append(os.path.join(root, name))
    return paths


def read_any(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()

    if ext in {".txt", ".md"}:
        return read_text_file(path)

    if ext == ".pdf":
        return read_pdf_file(path)

    if ext == ".csv":
        return read_csv_file(path)

    return ""


def ingest_folder(base_dir: str):
    files = discover_files(base_dir)
    print(f"📁 Found {len(files)} files to ingest.")

    for path in files:
        try:
            raw_text = read_any(path)

            if not raw_text.strip():
                print(f"⚠️  Skipping empty file: {path}")
                continue

            doc_id = str(uuid.uuid4())
            chunks = list(chunk_text(raw_text))
            embeddings = embed_texts(chunks)

            points = []
            for i, (chunk, vec) in enumerate(zip(chunks, embeddings)):
                points.append(
                    qm.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vec,
                        payload={
                            "doc_id": doc_id,
                            "filename": os.path.basename(path),
                            "source_path": path,
                            "ext": os.path.splitext(path)[1],
                            "text": chunk,
                            "chunk": i,
                        },
                    )
                )

            upsert_points(points)

            # Log ingestion record
            pg_execute(
                """
                INSERT INTO ingested_documents
                (doc_id, filename, source_path, num_chunks, status)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (doc_id, os.path.basename(path), path, len(points), "success"),
            )

            print(f"✅ Ingested {path} → {len(points)} chunks")

        except Exception as e:
            print(f"❌ Error ingesting {path}: {e}")

