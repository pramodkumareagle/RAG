from core.github.loader import get_repo_tree, get_file_content
from core.github.chunker import chunk_code
from core.embeddings.embedder import embed_texts
from core.vector.store import upsert_snippet

def ingest_public_repo(owner: str, repo: str):
    tree = get_repo_tree(owner, repo)

    code_chunks = []
    metadatas = []

    for file in tree:
        if not file["path"].endswith(".py"):
            continue

        code = get_file_content(owner, repo, file["path"])
        chunks = chunk_code("python", code)

        for chunk in chunks:
            if len(chunk.strip()) < 50:
                continue

            code_chunks.append(chunk)
            metadatas.append({
                "repo": f"{owner}/{repo}",
                "file": file["path"],
                "language": "python"
            })

    # 🔥 YOUR embedder used here
    embeddings = embed_texts(code_chunks)

    for emb, meta, content in zip(embeddings, metadatas, code_chunks):
        upsert_snippet(
            embedding=emb,
            content=content,
            metadata=meta
        )
