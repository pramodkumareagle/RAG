from fastapi import APIRouter
from pydantic import BaseModel
from mistralai import Mistral

from core.github.realtime_search import (
    github_code_search,
    get_file_download_url,
    fetch_raw_file,
    extract_snippet,
)

router = APIRouter()
client = Mistral(api_key=None)  # uses env MISTRAL_API_KEY if set

SYSTEM_PROMPT = """
You are a senior software engineer.
Use ONLY the provided GitHub code snippets.
Return real code blocks.
Mention repo and file names.
If snippets are not enough, say what is missing.
"""

class CodeChatRequest(BaseModel):
    question: str


@router.post("/v1/code-snippet-chat")
def code_chat(payload: CodeChatRequest):
    question = payload.question.strip()

    # Build GitHub search query (public)
    # You can tune this: add language filters etc.
    gh_query = f"{question} language:python"

    items = github_code_search(gh_query, per_page=5)

    if not items:
        return {"answer": "No relevant code found on GitHub search for this query.", "sources": []}

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
        return {"answer": "GitHub search found matches, but I couldn't fetch the raw files.", "sources": sources}

    prompt = f"Question: {question}\n\nGitHub snippets:\n\n" + "\n\n---\n\n".join(context_blocks)

    resp = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
    )

    return {
        "answer": resp.choices[0].message["content"],
        "sources": sources
    }
