"""
ncode — DSA Question Bank
SQLite-backed question bank with Striver's SDE Sheet and NeetCode 150 questions.
Provides search, filter by difficulty/status/sheet/topic.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# DB lives next to this file so it's bundled with the app
DB_PATH = Path(__file__).parent / "questions.db"


@dataclass
class Question:
    id: int
    title: str
    source: str            # "Striver" | "NeetCode" | "Both"
    topic: str             # "Arrays", "Linked List", "Trees", …
    difficulty: str        # "Easy" | "Medium" | "Hard"
    problem_statement: str
    examples: str
    constraints: str
    time_complexity: str
    space_complexity: str
    lc_number: int = 0     # LeetCode problem number (0 = none)
    tags: str = ""         # comma-separated extra tags


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Idempotent."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS questions (
            id                INTEGER PRIMARY KEY,
            title             TEXT NOT NULL,
            source            TEXT NOT NULL,
            topic             TEXT NOT NULL,
            difficulty        TEXT NOT NULL,
            problem_statement TEXT NOT NULL,
            examples          TEXT NOT NULL DEFAULT '',
            constraints       TEXT NOT NULL DEFAULT '',
            time_complexity   TEXT NOT NULL DEFAULT '',
            space_complexity  TEXT NOT NULL DEFAULT '',
            lc_number         INTEGER NOT NULL DEFAULT 0,
            tags              TEXT NOT NULL DEFAULT ''
        );
    """)
    conn.commit()
    conn.close()


def get_all_questions() -> list[Question]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM questions ORDER BY source, topic, difficulty").fetchall()
    conn.close()
    return [_row_to_q(r) for r in rows]


def get_question(qid: int) -> Optional[Question]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
    conn.close()
    return _row_to_q(row) if row else None


def search_questions(
    query: str = "",
    sheet: str = "All",
    topic: str = "All",
    difficulty: str = "All",
) -> list[Question]:
    """Filter questions. All params are optional."""
    sql = "SELECT * FROM questions WHERE 1=1"
    params: list = []
    if query:
        sql += " AND (title LIKE ? OR problem_statement LIKE ? OR tags LIKE ?)"
        q = f"%{query}%"
        params += [q, q, q]
    if sheet != "All":
        sql += " AND (source=? OR source='Both')"
        params.append(sheet)
    if topic != "All":
        sql += " AND topic=?"
        params.append(topic)
    if difficulty != "All":
        sql += " AND difficulty=?"
        params.append(difficulty)
    sql += " ORDER BY topic, difficulty, title"
    conn = _get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [_row_to_q(r) for r in rows]


def get_topics() -> list[str]:
    conn = _get_conn()
    rows = conn.execute("SELECT DISTINCT topic FROM questions ORDER BY topic").fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_question_count() -> dict[str, int]:
    """Return {'total': N, 'Striver': N, 'NeetCode': N}"""
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    striver = conn.execute(
        "SELECT COUNT(*) FROM questions WHERE source IN ('Striver','Both')"
    ).fetchone()[0]
    neetcode = conn.execute(
        "SELECT COUNT(*) FROM questions WHERE source IN ('NeetCode','Both')"
    ).fetchone()[0]
    conn.close()
    return {"total": total, "Striver": striver, "NeetCode": neetcode}


def _row_to_q(row: sqlite3.Row) -> Question:
    return Question(
        id=row["id"],
        title=row["title"],
        source=row["source"],
        topic=row["topic"],
        difficulty=row["difficulty"],
        problem_statement=row["problem_statement"],
        examples=row["examples"],
        constraints=row["constraints"],
        time_complexity=row["time_complexity"],
        space_complexity=row["space_complexity"],
        lc_number=row["lc_number"],
        tags=row["tags"],
    )
