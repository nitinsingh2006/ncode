"""
ncode — DSA Solution Storage
Persists user solutions, tracks solved/unsolved status per question.
DB stored in ~/.config/nitin-editor/dsa_solutions.db (user-writable).
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.settings import CONFIG_DIR

SOLUTIONS_DB = CONFIG_DIR / "dsa_solutions.db"


@dataclass
class Solution:
    question_id: int
    language: str
    code: str
    solved: bool
    saved_at: str  # ISO datetime string


def init_solutions_db() -> None:
    """Create solutions table. Idempotent."""
    SOLUTIONS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS solutions (
            question_id  INTEGER PRIMARY KEY,
            language     TEXT    NOT NULL DEFAULT 'Python',
            code         TEXT    NOT NULL DEFAULT '',
            solved       INTEGER NOT NULL DEFAULT 0,
            saved_at     TEXT    NOT NULL DEFAULT ''
        );
    """)
    conn.commit()
    conn.close()


def save_solution(question_id: int, language: str, code: str, solved: bool = True) -> None:
    """Upsert a solution for the given question."""
    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO solutions (question_id, language, code, solved, saved_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(question_id) DO UPDATE SET
            language=excluded.language,
            code=excluded.code,
            solved=excluded.solved,
            saved_at=excluded.saved_at
        """,
        (question_id, language, code, 1 if solved else 0, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_solution(question_id: int) -> Optional[Solution]:
    """Return the saved solution for a question, or None."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM solutions WHERE question_id=?", (question_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return Solution(
        question_id=row["question_id"],
        language=row["language"],
        code=row["code"],
        solved=bool(row["solved"]),
        saved_at=row["saved_at"],
    )


def get_solved_ids() -> set[int]:
    """Return the set of question_ids that are marked solved."""
    conn = _get_conn()
    rows = conn.execute("SELECT question_id FROM solutions WHERE solved=1").fetchall()
    conn.close()
    return {r[0] for r in rows}


def get_progress() -> dict:
    """Return overall progress stats."""
    conn = _get_conn()
    total_solved = conn.execute("SELECT COUNT(*) FROM solutions WHERE solved=1").fetchone()[0]
    conn.close()
    return {"total_solved": total_solved}


def get_topic_progress(questions: list) -> dict[str, tuple[int, int]]:
    """
    Given a list of Question objects, return per-topic (solved, total) counts.
    Returns: {'Arrays': (3, 10), 'Trees': (1, 8), ...}
    """
    solved_ids = get_solved_ids()
    result: dict[str, list[int]] = {}
    for q in questions:
        t = q.topic
        if t not in result:
            result[t] = [0, 0]
        result[t][1] += 1
        if q.id in solved_ids:
            result[t][0] += 1
    return {t: (v[0], v[1]) for t, v in result.items()}


def _get_conn() -> sqlite3.Connection:
    SOLUTIONS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SOLUTIONS_DB))
    conn.row_factory = sqlite3.Row
    return conn
