from core.github.loader import get_repo_tree, get_file_content
from core.github.chunker import chunk_code
from core.embeddings.embedder import embed_text
from core.vector.store import store_snippet

def ingest_repo(owner, repo):
    tree = get_repo_tree(owner, repo)

    for f in tree:
        if f["path"].endswith(".py"):
            code = get_file_content(owner, repo, f["path"])
            chunks = chunk_code("python", code)
            embeddings = embed_text(chunks)

            for chunk, emb in zip(chunks, embeddings):
                store_snippet({
                    "repo": f"{owner}/{repo}",
                    "file": f["path"],
                    "language": "python",
                    "content": chunk
                }, emb.embedding)
