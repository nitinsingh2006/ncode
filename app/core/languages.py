"""Canonical language and file-extension definitions shared by all clients."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

LANGUAGES = ["Python", "C", "C++", "Java", "JavaScript", "HTML", "CSS", "SQL"]
LANGUAGE_EXTENSIONS = {
    "Python": ".py", "C": ".c", "C++": ".cpp", "Java": ".java",
    "JavaScript": ".js", "HTML": ".html", "CSS": ".css", "SQL": ".sql",
}
EXTENSION_MAP = {
    ".py": "Python", ".c": "C", ".cpp": "C++", ".cc": "C++", ".cxx": "C++",
    ".java": "Java", ".js": "JavaScript", ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".sql": "SQL", ".db": "SQL", ".sqlite": "SQL", ".sqlite3": "SQL",
}


def detect_language(file_path: str | Path) -> Optional[str]:
    return EXTENSION_MAP.get(Path(file_path).suffix.lower())
