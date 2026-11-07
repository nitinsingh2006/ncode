"""
Nitin Editor — app/github_pusher.py
GitHub push helper using GitHub REST API (urllib only, no extra deps).

Speed strategy:
  - Optimistic PUT (no SHA pre-fetch) — saves 1 round-trip per file
  - If GitHub returns 422 (file exists, needs SHA) → GET sha then retry
  - DSA: both files pushed in parallel threads → 2 round-trips instead of 4
"""
from __future__ import annotations

import base64
import json
import re
import threading
import urllib.error
import urllib.request
from typing import Optional


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_owner_repo(repo_url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL (https or git@)."""
    repo_url = repo_url.strip().rstrip("/")
    m = re.match(r"git@github\.com:([^/]+)/(.+?)(?:\.git)?$", repo_url)
    if m:
        return m.group(1), m.group(2)
    m = re.match(r"https?://github\.com/([^/]+)/(.+?)(?:\.git)?$", repo_url)
    if m:
        return m.group(1), m.group(2)
    raise ValueError(f"Cannot parse GitHub URL: {repo_url!r}")


def _lang_to_ext(language: str) -> str:
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


def _make_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "ncode-editor/1.0",
    }


def _create_repo(owner: str, repo: str, token: str) -> None:
    """Create a GitHub repo via API if it does not exist."""
    url = "https://api.github.com/user/repos"
    body = {
        "name": repo,
        "description": "Created by ncode editor",
        "private": False,
        "auto_init": True,   # creates default branch with README so contents API works
    }
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers=_make_headers(token),
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as _:
            pass  # 201 Created
    except urllib.error.HTTPError as e:
        body_text = e.read().decode(errors="replace")
        if e.code == 422:
            pass  # repo already exists — fine
        else:
            raise RuntimeError(f"Cannot create repo: {e.code}: {body_text}") from e


def _put_file(
    owner: str,
    repo: str,
    file_path: str,
    token: str,
    content_b64: str,
    commit_msg: str,
) -> None:
    """
    Optimistic PUT — no pre-fetch of SHA.
    - 201/200 → success (new/updated file)
    - 404     → repo missing → auto-create repo → retry
    - 422     → file exists, need SHA → GET sha → retry once
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    headers = _make_headers(token)

    def _do_put(sha: Optional[str] = None) -> None:
        body: dict = {"message": commit_msg, "content": content_b64}
        if sha:
            body["sha"] = sha
        req = urllib.request.Request(
            url, data=json.dumps(body).encode(), method="PUT", headers=headers
        )
        with urllib.request.urlopen(req, timeout=20) as _:
            pass

    try:
        _do_put()
    except urllib.error.HTTPError as e:
        body_text = e.read().decode(errors="replace")
        if e.code == 404:
            # Repo doesn't exist → create it, then retry
            _create_repo(owner, repo, token)
            import time; time.sleep(1)  # give GitHub a moment to initialise
            try:
                _do_put()
            except urllib.error.HTTPError as e2:
                bt2 = e2.read().decode(errors="replace")
                if e2.code == 422:
                    # auto_init created README → need sha for any existing file
                    get_req = urllib.request.Request(url, method="GET", headers=headers)
                    try:
                        with urllib.request.urlopen(get_req, timeout=10) as r:
                            sha = json.loads(r.read().decode()).get("sha")
                        _do_put(sha)
                    except urllib.error.HTTPError as e3:
                        raise RuntimeError(f"GitHub API {e3.code}: {e3.read().decode(errors='replace')}") from e3
                else:
                    raise RuntimeError(f"GitHub API {e2.code}: {bt2}") from e2
        elif e.code == 422:
            # File exists and needs SHA
            get_req = urllib.request.Request(url, method="GET", headers=headers)
            try:
                with urllib.request.urlopen(get_req, timeout=10) as r:
                    sha = json.loads(r.read().decode()).get("sha")
                _do_put(sha)
            except urllib.error.HTTPError as e2:
                raise RuntimeError(f"GitHub API {e2.code}: {e2.read().decode(errors='replace')}") from e2
        else:
            raise RuntimeError(f"GitHub API {e.code}: {body_text}") from e


# ── Public API ────────────────────────────────────────────────────────────────

def push_code_file(
    repo_url: str,
    token: str,
    filename: str,
    language: str,
    code: str,
    commit_msg: str = "",
    subfolder: str = "code",
) -> tuple[bool, str]:
    """Push a single code file. Returns (success, message)."""
    if not repo_url or not token:
        return False, "GitHub repo URL or token not configured."
    try:
        owner, repo = _parse_owner_repo(repo_url)
    except ValueError as e:
        return False, str(e)

    ext = _lang_to_ext(language)
    base = re.sub(r"\.[^.]+$", "", filename)  # drop extension
    base = re.sub(r"[\u25cf\s]+", " ", base).strip()  # strip bullet ● and spaces
    base = re.sub(r'[\\/:*?"<>|\u25cf\t\n\r]+', "_", base)  # bad chars→_
    base = re.sub(r"_+", "_", base).strip("_ ") or "untitled"
    file_path = f"{subfolder}/{base}.{ext}" if subfolder else f"{base}.{ext}"
    content_b64 = base64.b64encode(code.encode()).decode()
    msg = commit_msg or f"ncode: add/update {base}.{ext}"

    try:
        _put_file(owner, repo, file_path, token, content_b64, msg)
        return True, f"✅ Pushed → {owner}/{repo}/{file_path}"
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
    Push DSA solution to DSA repo.
    Both README.md and solution.{ext} pushed in PARALLEL threads.
    Returns (success, message).
    """
    if not repo_url or not token:
        return False, "DSA GitHub repo URL or token not configured."
    try:
        owner, repo = _parse_owner_repo(repo_url)
    except ValueError as e:
        return False, str(e)

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", question_title).strip("_").lower()
    topic_slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic).strip("_").lower() if topic else "misc"
    folder = f"{topic_slug}/{slug}"
    ext = _lang_to_ext(language)
    commit_msg = f"dsa: {question_title} — {language} solution"

    readme = f"""# {question_title}

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

    files = [
        (f"{folder}/README.md",        readme),
        (f"{folder}/solution.{ext}",   code),
    ]

    errors: list[str] = []
    lock = threading.Lock()

    def _push_one(file_path: str, content: str) -> None:
        b64 = base64.b64encode(content.encode()).decode()
        try:
            _put_file(owner, repo, file_path, token, b64, commit_msg)
        except RuntimeError as e:
            with lock:
                errors.append(f"{file_path.split('/')[-1]}: {e}")

    # Fire both uploads in parallel
    threads = [
        threading.Thread(target=_push_one, args=(fp, ct), daemon=True)
        for fp, ct in files
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if errors:
        return False, "Some files failed:\n" + "\n".join(errors)
    return True, f"✅ DSA pushed → {owner}/{repo}/{folder}/"
