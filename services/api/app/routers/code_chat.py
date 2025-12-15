from fastapi import APIRouter
from core.embeddings.embedder import embed_text
from core.vector.store import search_snippets
from mistralai import Mistral

router = APIRouter()
client = Mistral()

SYSTEM_PROMPT = """
You are a senior software engineer.
Use ONLY the provided code snippets.
Return real code blocks.
Mention repo and file names.
"""

@router.post("/v1/code-snippet-chat")
def code_chat(question: str):
    # 🔥 Embed user query
    query_vec = embed_text(question)

    snippets = search_snippets(query_vec, top_k=5)

    if not snippets:
        return {"answer": "No relevant code found in indexed repositories."}

    context = "\n\n".join(
        f"Repo: {s['repo']} | File: {s['file']}\n{s['content']}"
        for s in snippets
    )

    resp = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{question}\n\n{context}"}
        ]
    )

    return {"answer": resp.choices[0].message["content"]}
