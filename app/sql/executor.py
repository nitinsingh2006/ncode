"""
Nitin Editor - sql/executor.py
Execute SQL scripts against a local SQLite database.

Uses Python's built-in sqlite3 module — no external SQL server required.
No network, no cloud, fully offline.
"""
from __future__ import annotations

import sqlite3
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from .formatter import format_table, format_rowcount


@dataclass
class SQLResult:
    """Result of executing a SQL script."""
    output: str = ""          # Formatted results/messages
    error: str = ""           # Error message if any
    elapsed_time: float = 0.0
    statement_count: int = 0
    success: bool = True


class SQLExecutor:
    """
    Execute SQL scripts using Python's built-in sqlite3.

    Supports:
    - Temporary in-memory or temp-file databases (default)
    - Persistent .db/.sqlite/.sqlite3 files
    - Multiple statements per script
    - SELECT with formatted table output
    - DDL (CREATE, DROP, ALTER)
    - DML (INSERT, UPDATE, DELETE)
    """

    def __init__(self) -> None:
        self._temp_db_path: Optional[Path] = None

    def execute(
        self,
        sql_script: str,
        db_path: Optional[Path] = None,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> SQLResult:
        """
        Execute a SQL script and return a SQLResult.

        Args:
            sql_script: The SQL text to execute.
            db_path: Path to a .db file. If None, a temporary database is used.
            on_output: Optional callback for streaming output lines.
        """
        result = SQLResult()
        start = time.monotonic()

        if not sql_script.strip():
            result.output = "⚠  No SQL to execute.\n"
            result.success = False
            result.elapsed_time = 0.0
            return result

        # Determine database connection target
        use_temp = db_path is None
        if use_temp:
            # Use a temp file so we can reset state between runs
            tmp = tempfile.NamedTemporaryFile(
                prefix="ncode_sql_", suffix=".db", delete=False
            )
            tmp.close()
            self._temp_db_path = Path(tmp.name)
            conn_target = str(self._temp_db_path)
        else:
            self._temp_db_path = None
            conn_target = str(db_path)

        output_parts: list[str] = []

        def _emit(text: str) -> None:
            output_parts.append(text)
            if on_output:
                on_output(text)

        try:
            conn = sqlite3.connect(conn_target)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Split script into individual statements
            statements = self._split_statements(sql_script)
            stmt_count = 0

            for stmt in statements:
                stmt = stmt.strip()
                if not stmt:
                    continue
                stmt_count += 1

                try:
                    cursor.execute(stmt)
                    conn.commit()

                    keyword = stmt.split()[0].upper() if stmt else ""

                    if keyword == "SELECT" or cursor.description:
                        # Fetch and format results
                        rows = cursor.fetchall()
                        if cursor.description:
                            columns = [desc[0] for desc in cursor.description]
                            plain_rows = [tuple(row) for row in rows]
                            table = format_table(columns, plain_rows)
                            _emit(table + "\n")
                        else:
                            _emit("(query returned no description)\n\n")
                    elif keyword in ("INSERT", "UPDATE", "DELETE", "REPLACE"):
                        count = cursor.rowcount
                        _emit(format_rowcount(keyword, max(count, 0)))
                        _emit("\n")
                    else:
                        # DDL or other — just confirm
                        _emit(f"OK: {stmt[:60]}{'…' if len(stmt) > 60 else ''}\n\n")

                except sqlite3.Error as e:
                    _emit(f"SQL Error:\n  {e}\n\nStatement:\n  {stmt[:120]}\n\n")
                    result.success = False

            result.statement_count = stmt_count
            if stmt_count == 0 and not output_parts:
                _emit("⚠  No SQL statements to execute.\n")
                result.success = False
            conn.close()

        except sqlite3.Error as e:
            result.error = f"Database error: {e}"
            result.success = False
        except Exception as e:
            result.error = f"Unexpected error: {e}"
            result.success = False
        finally:
            if use_temp and self._temp_db_path:
                try:
                    self._temp_db_path.unlink(missing_ok=True)
                except Exception:
                    pass
                self._temp_db_path = None

        result.output = "".join(output_parts)
        result.elapsed_time = time.monotonic() - start
        return result

    def _split_statements(self, script: str) -> list[str]:
        """
        Split a SQL script into individual statements on semicolons,
        respecting single-quoted strings and -- comments.
        Simple but effective for standard SQL.
        """
        statements: list[str] = []
        current: list[str] = []
        in_string = False
        string_char = ""
        i = 0

        while i < len(script):
            ch = script[i]

            if in_string:
                current.append(ch)
                if ch == string_char:
                    # Check for escaped quote ('')
                    if i + 1 < len(script) and script[i + 1] == string_char:
                        current.append(script[i + 1])
                        i += 2
                        continue
                    in_string = False
            elif ch in ("'", '"'):
                in_string = True
                string_char = ch
                current.append(ch)
            elif ch == "-" and i + 1 < len(script) and script[i + 1] == "-":
                # Line comment: skip to end of line
                while i < len(script) and script[i] != "\n":
                    i += 1
                continue
            elif ch == ";":
                stmt = "".join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
            else:
                current.append(ch)

            i += 1

        # Trailing statement without semicolon
        remaining = "".join(current).strip()
        if remaining:
            statements.append(remaining)

        return statements
