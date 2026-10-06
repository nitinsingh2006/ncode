"""
Nitin Editor - terminal/history.py
Persistent terminal command history stored locally.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

HISTORY_FILE = Path.home() / ".config" / "nitin-editor" / "terminal_history.json"
MAX_HISTORY = 500


def load_history() -> list[str]:
    """Load command history from disk. Returns empty list on any error."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(item) for item in data[:MAX_HISTORY]]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_history(history: list[str]) -> None:
    """Save command history to disk, capped at MAX_HISTORY entries."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    trimmed = history[:MAX_HISTORY]
    try:
        with HISTORY_FILE.open("w", encoding="utf-8") as f:
            json.dump(trimmed, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def add_command(history: list[str], command: str, max_size: int = MAX_HISTORY) -> list[str]:
    """
    Add a command to history, deduplicating consecutive repeats.
    Returns the updated list.
    """
    command = command.strip()
    if not command:
        return history
    # Remove duplicate if it was the previous command
    new_history = [c for c in history if c != command]
    new_history.insert(0, command)
    return new_history[:max_size]
