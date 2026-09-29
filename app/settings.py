"""
Nitin Editor - settings.py
Application-wide settings and configuration management.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "nitin-editor"
CONFIG_FILE = CONFIG_DIR / "settings.json"
RECENT_FILES_FILE = CONFIG_DIR / "recent_files.json"

DEFAULTS: dict[str, Any] = {
    "theme": "dark",
    "font_size": 14,
    "tab_size": 4,
    "word_wrap": False,
    "execution_timeout": 10,
    "font_family": "JetBrains Mono,Fira Code,Consolas,Courier New,monospace",
}


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict[str, Any]:
    _ensure_config_dir()
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge with defaults so new keys are always present
            merged = {**DEFAULTS, **data}
            return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULTS)


def save_settings(settings: dict[str, Any]) -> None:
    _ensure_config_dir()
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


def load_recent_files() -> list[str]:
    _ensure_config_dir()
    if RECENT_FILES_FILE.exists():
        try:
            with RECENT_FILES_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return [p for p in data if Path(p).exists()]
        except (json.JSONDecodeError, OSError):
            pass
    return []


def add_recent_file(path: str) -> None:
    _ensure_config_dir()
    files = load_recent_files()
    # Remove duplicate, put at front
    files = [f for f in files if f != path]
    files.insert(0, path)
    files = files[:20]  # keep only 20 recent
    with RECENT_FILES_FILE.open("w", encoding="utf-8") as f:
        json.dump(files, f, indent=2)
