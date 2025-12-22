from fastapi import APIRouter, Depends
from pydantic import BaseModel
from mistralai import Mistral
import os
import uuid
from datetime import datetime

from core.storage.postgres_client import execute
from services.api.app.auth.deps import get_current_user

from core.github.realtime_search import (
    github_code_search,
    get_file_download_url,
    fetch_raw_file,
    extract_snippet,
)

router = APIRouter()
client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

SYSTEM_PROMPT = """
You are a senior software engineer.
Use ONLY the provided GitHub code snippets.
Return real code blocks.
Mention repo and file names.
If snippets are not enough, say what is missing.
"""

class CodeChatRequest(BaseModel):
    question: str
    session_id: str | None = None  # ✅ optional, UI can pass it for persistent sessions


@router.post("/v1/code-snippet-chat")
def code_chat(payload: CodeChatRequest, user=Depends(get_current_user)):
    question = payload.question.strip()
    if not question:
        return {"answer": "Question is required.", "sources": []}

    user_id = str(user["id"])
    session_id = payload.session_id or f"codechat-{user_id}-{datetime.utcnow().date().isoformat()}"

    # ✅ log user message (optional)
    execute(
        """
        INSERT INTO code_chat_history (session_id, role, content, source, created_at)
        VALUES (%s, 'user', %s, %s, now())
        """,
        (session_id, question, None)
    )

    # Build GitHub search query (public)
    gh_query = f"{question} language:python"
    items = github_code_search(gh_query, per_page=5)

    if not items:
        answer = "No relevant code found on GitHub search for this query."
        # ✅ log assistant message
        execute(
            """
            INSERT INTO code_chat_history (session_id, role, content, source, created_at)
            VALUES (%s, 'assistant', %s, %s, now())
            """,
            (session_id, answer, "[]")
        )
        return {"answer": answer, "sources": []}

    sources = []
    context_blocks = []

    for it in items:
        repo_full = it["repository"]["full_name"]  # owner/repo
        owner, repo = repo_full.split("/", 1)
        path = it["path"]

        download_url = get_file_download_url(owner, repo, path)
        if not download_url:
            continue

        try:
            content = fetch_raw_file(download_url)
        except Exception:
            continue

        snippet = extract_snippet(content, question)

        file_url = it.get("html_url") or f"https://github.com/{repo_full}/blob/main/{path}"

        sources.append({
            "repo": repo_full,
            "file": path,
            "url": file_url
        })

        context_blocks.append(
            f"Repo: {repo_full}\nFile: {path}\nURL: {file_url}\n\n```python\n{snippet}\n```"
        )

    if not context_blocks:
        answer = "GitHub search found matches, but I couldn't fetch the raw files."

        execute(
            """
            INSERT INTO code_chat_history (session_id, role, content, source, created_at)
            VALUES (%s, 'assistant', %s, %s, now())
            """,
            (session_id, answer, str(sources))
        )

        return {"answer": answer, "sources": sources}

    prompt = f"Question: {question}\n\nGitHub snippets:\n\n" + "\n\n---\n\n".join(context_blocks)

    resp = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
    )

    answer = resp.choices[0].message.content

    # ✅ log assistant message (sources stored as JSON-ish string)
    execute(
        """
        INSERT INTO code_chat_history (session_id, role, content, source, created_at)
        VALUES (%s, 'assistant', %s, %s, now())
        """,
        (session_id, answer, str(sources))
    )

    return {
        "answer": answer,
        "sources": sources
    }
