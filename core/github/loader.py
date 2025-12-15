import requests
from .client import HEADERS

def get_repo_tree(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
    return requests.get(url, headers=HEADERS).json()["tree"]

def get_file_content(owner, repo, path):
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}"
    return requests.get(url).text
