import time
import requests
import os

INDEX_NAME  = os.getenv("INDEX_NAME", "docs")
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DATA_DIR    = os.getenv("DATA_DIR", "./data")


def wait_for_qdrant(url="http://qdrant:6333/health"):
    print("⏳ Waiting for Qdrant to be ready...")

    for _ in range(30):
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                print("✅ Qdrant is ready.")
                return
        except:
            pass

        time.sleep(2)

    raise RuntimeError("❌ Qdrant did not become ready in time!")
