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
    "auto_save": False,
    "default_language": "Python",
    # SQL settings
    "sql_db_mode": "Temporary",   # "Temporary" or "File"
    "sql_auto_cleanup": True,
    # Terminal settings
    "terminal_default_os": "Linux",
    "terminal_timeout": 30,
    "terminal_history_size": 500,
    "terminal_confirm_dangerous": True,
    # Kept portable: UI clients may display the detected platform without
    # persisting machine-specific paths or secrets.
    "mobile_editor_font_size": 16,
    "mobile_touch_controls": True,
    "mobile_keyboard_behavior": "resize",
    "mobile_landscape_editor_mode": True,
}


def migrate_settings(data: dict[str, Any]) -> dict[str, Any]:
    """Merge every historical settings file into the current portable schema."""
    return {**DEFAULTS, **data}


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict[str, Any]:
    _ensure_config_dir()
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge with defaults so new keys are always present
            return migrate_settings(data)
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULTS)


def save_settings(settings: dict[str, Any]) -> None:
    try:
        _ensure_config_dir()
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(migrate_settings(settings), f, indent=2)
    except OSError:
        # A read-only profile must not make closing the editor fail.  Settings
        # remain active for this session and no data is silently redirected.
        return


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
