"""
Nitin Editor — app/github_pusher.py
GitHub push helper using GitHub REST API (urllib only, no extra deps).

Supports:
  - push_code_file()   : push any code file to a GitHub repo
  - push_dsa_solution(): push DSA problem + solution to a separate repo
"""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _parse_owner_repo(repo_url: str) -> tuple[str, str]:
    """
    Extract (owner, repo) from a GitHub URL.
    Accepts formats:
      https://github.com/owner/repo
      https://github.com/owner/repo.git
      git@github.com:owner/repo.git
    """
    repo_url = repo_url.strip().rstrip("/")
    # git@github.com:owner/repo.git
    m = re.match(r"git@github\.com:([^/]+)/(.+?)(?:\.git)?$", repo_url)
    if m:
        return m.group(1), m.group(2)
    # https://github.com/owner/repo[.git]
    m = re.match(r"https?://github\.com/([^/]+)/(.+?)(?:\.git)?$", repo_url)
    if m:
        return m.group(1), m.group(2)
    raise ValueError(f"Cannot parse GitHub URL: {repo_url!r}")


def _lang_to_ext(language: str) -> str:
    """Map language name to file extension."""
    _MAP = {
        "Python": "py", "C++": "cpp", "C": "c", "Java": "java",
        "JavaScript": "js", "TypeScript": "ts", "Go": "go", "Rust": "rs",
        "Ruby": "rb", "Kotlin": "kt", "Swift": "swift", "PHP": "php",
        "C#": "cs", "Scala": "scala", "R": "r", "Dart": "dart",
        "Lua": "lua", "Haskell": "hs", "Perl": "pl", "SQL": "sql",
        "Bash": "sh", "HTML": "html", "CSS": "css", "YAML": "yaml",
        "TOML": "toml", "JSON": "json", "Markdown": "md", "Text": "txt",
    }
    return _MAP.get(language, "txt")


def _github_api_request(
    method: str,
    path: str,
    token: str,
    body: Optional[dict] = None,
) -> dict:
    """Make a GitHub REST API request. Returns parsed JSON response."""
    url = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "ncode-editor/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode(errors="replace")
        raise RuntimeError(f"GitHub API {e.code}: {body_text}") from e


def _get_file_sha(owner: str, repo: str, path: str, token: str) -> Optional[str]:
    """Return the SHA of an existing file, or None if it doesn't exist."""
    try:
        resp = _github_api_request(
            "GET", f"/repos/{owner}/{repo}/contents/{path}", token
        )
        return resp.get("sha")
    except RuntimeError as e:
        if "404" in str(e):
            return None
        raise


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def push_code_file(
    repo_url: str,
    token: str,
    filename: str,
    language: str,
    code: str,
    commit_msg: str = "",
    subfolder: str = "code",
) -> tuple[bool, str]:
    """
    Push a single code file to the given GitHub repo.

    Returns (success: bool, message: str).
    """
    if not repo_url or not token:
        return False, "GitHub repo URL or token not configured."
    try:
        owner, repo = _parse_owner_repo(repo_url)
    except ValueError as e:
        return False, str(e)

    ext = _lang_to_ext(language)
    # Clean filename: strip extension, add correct one
    base = re.sub(r"\.[^.]+$", "", filename) or "untitled"
    # Sanitize path chars
    base = re.sub(r'[\\/:*?"<>|]', "_", base)
    file_path = f"{subfolder}/{base}.{ext}" if subfolder else f"{base}.{ext}"

    content_b64 = base64.b64encode(code.encode()).decode()
    sha = _get_file_sha(owner, repo, file_path, token)

    msg = commit_msg or f"ncode: add/update {base}.{ext}"
    body: dict = {"message": msg, "content": content_b64}
    if sha:
        body["sha"] = sha

    try:
        _github_api_request("PUT", f"/repos/{owner}/{repo}/contents/{file_path}", token, body)
        return True, f"✅ Pushed to {owner}/{repo}/{file_path}"
    except RuntimeError as e:
        return False, f"Push failed: {e}"


def push_dsa_solution(
    repo_url: str,
    token: str,
    question_title: str,
    question_statement: str,
    topic: str,
    difficulty: str,
    language: str,
    code: str,
) -> tuple[bool, str]:
    """
    Push a DSA solution to the DSA GitHub repo.

    Creates:
      {topic}/{slug}/README.md   ← problem statement
      {topic}/{slug}/solution.{ext}  ← user's code

    Returns (success: bool, message: str).
    """
    if not repo_url or not token:
        return False, "DSA GitHub repo URL or token not configured."
    try:
        owner, repo = _parse_owner_repo(repo_url)
    except ValueError as e:
        return False, str(e)

    # Build folder slug
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", question_title).strip("_").lower()
    topic_slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic).strip("_").lower() if topic else "misc"
    folder = f"{topic_slug}/{slug}"

    ext = _lang_to_ext(language)

    # README.md content
    readme_content = f"""# {question_title}

**Topic:** {topic}  
**Difficulty:** {difficulty}  
**Language:** {language}  

---

## Problem Statement

{question_statement}

---

## My Solution

See [`solution.{ext}`](./solution.{ext})
"""

    errors = []
    pushed = []

    for file_name, content in [
        ("README.md", readme_content),
        (f"solution.{ext}", code),
    ]:
        file_path = f"{folder}/{file_name}"
        content_b64 = base64.b64encode(content.encode()).decode()
        sha = _get_file_sha(owner, repo, file_path, token)
        body: dict = {
            "message": f"dsa: {question_title} — {language} solution",
            "content": content_b64,
        }
        if sha:
            body["sha"] = sha
        try:
            _github_api_request("PUT", f"/repos/{owner}/{repo}/contents/{file_path}", token, body)
            pushed.append(file_name)
        except RuntimeError as e:
            errors.append(f"{file_name}: {e}")

    if errors:
        return False, "Some files failed:\n" + "\n".join(errors)
    return True, f"✅ DSA solution pushed → {owner}/{repo}/{folder}/"
