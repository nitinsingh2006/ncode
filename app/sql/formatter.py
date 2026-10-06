"""
Nitin Editor - sql/formatter.py
Format SQLite query results as readable ASCII tables.
"""
from __future__ import annotations

from typing import Any


def format_table(columns: list[str], rows: list[tuple[Any, ...]]) -> str:
    """
    Format query results as a readable ASCII table.

    Example output:
        +----+-------+-------+
        | id | name  | marks |
        +----+-------+-------+
        | 1  | Amit  | 85    |
        | 2  | Rahul | 92    |
        +----+-------+-------+
        2 row(s) returned.
    """
    if not columns:
        return "(no columns)\n"

    # Convert all values to strings
    str_rows = [[str(v) if v is not None else "NULL" for v in row] for row in rows]

    # Compute column widths
    col_widths = [len(col) for col in columns]
    for row in str_rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))

    def _separator() -> str:
        return "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    def _row_line(values: list[str]) -> str:
        cells = [f" {v:<{col_widths[i]}} " for i, v in enumerate(values)]
        return "|" + "|".join(cells) + "|"

    lines: list[str] = []
    sep = _separator()
    lines.append(sep)
    lines.append(_row_line(columns))
    lines.append(sep)
    for row in str_rows:
        lines.append(_row_line(row))
    lines.append(sep)

    row_count = len(rows)
    lines.append(f"{row_count} row(s) returned.")

    return "\n".join(lines) + "\n"


def format_rowcount(operation: str, count: int) -> str:
    """Format a non-SELECT result (INSERT, UPDATE, DELETE, etc.)."""
    return f"{operation}: {count} row(s) affected.\n"
