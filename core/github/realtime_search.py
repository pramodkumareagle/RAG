import os
import re
import requests
from typing import List, Dict, Optional

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()

BASE_HEADERS = {
    "Accept": "application/vnd.github+json",
}
if GITHUB_TOKEN:
    BASE_HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def github_code_search(query: str, per_page: int = 5) -> List[Dict]:
    """
    Real-time GitHub code search (public repos). Returns search items.
    """
    url = "https://api.github.com/search/code"
    params = {"q": query, "per_page": per_page}
    r = requests.get(url, headers=BASE_HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("items", [])


def get_file_download_url(owner: str, repo: str, path: str, ref: Optional[str] = None) -> Optional[str]:
    """
    Uses GitHub contents API to get a download_url for a file.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    params = {}
    if ref:
        params["ref"] = ref
    r = requests.get(url, headers=BASE_HEADERS, params=params, timeout=30)
    if r.status_code != 200:
        return None
    return r.json().get("download_url")


def fetch_raw_file(download_url: str) -> str:
    r = requests.get(download_url, timeout=30)
    r.raise_for_status()
    return r.text


def extract_snippet(content: str, query: str, max_lines: int = 60) -> str:
    """
    Extract a small snippet around first match of any query token.
    """
    lines = content.splitlines()
    tokens = [t for t in re.split(r"\s+", query) if t and ":" not in t]  # drop qualifiers like repo:, language:
    tokens = [t.strip().lower() for t in tokens if len(t.strip()) >= 3]

    # find first line index containing any token
    hit = None
    for i, line in enumerate(lines):
        low = line.lower()
        if any(tok in low for tok in tokens):
            hit = i
            break

    if hit is None:
        # fallback: just return first N lines
        return "\n".join(lines[:max_lines])

    start = max(0, hit - 15)
    end = min(len(lines), hit + 15)
    snippet = "\n".join(lines[start:end])
    return snippet[:8000]  # safety cap
