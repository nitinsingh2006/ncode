"""Small, UI-independent parsers for compiler and runtime diagnostics."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Diagnostic:
    severity: str  # "error", "warning", "info"
    message: str
    file: str = ""
    line: int | None = None
    column: int | None = None


_C_FAMILY = re.compile(
    r"^(?P<file>.*?):(?P<line>\d+):(?:(?P<column>\d+):)?\s*"
    r"(?P<severity>fatal error|error|warning|note):\s*(?P<message>.*)$",
    re.MULTILINE,
)
_JAVA_FAMILY = re.compile(
    r"^(?P<file>.*?\.java):(?P<line>\d+):\s*(?P<severity>error|warning):\s*(?P<message>.*)$",
    re.MULTILINE,
)
_PY_FILE = re.compile(r'^\s*File "(?P<file>.+?)", line (?P<line>\d+)', re.MULTILINE)
_PY_MESSAGE = re.compile(r"^(?P<severity>[A-Za-z]+Error|[A-Za-z]+Exception):\s*(?P<message>.*)$", re.MULTILINE)
_JS_LOCATION = re.compile(r"^(?P<file>.*?\.(?:js|ts)):(?P<line>\d+)$", re.MULTILINE)
_JS_MESSAGE = re.compile(r"^(?P<severity>[A-Za-z]+Error|[A-Za-z]+Exception):\s*(?P<message>.*)$", re.MULTILINE)


def parse_diagnostics(text: str, language: str = "") -> list[Diagnostic]:
    """Parse useful GCC/Clang, Python, Java, JS, and runtime locations without coupling to Qt."""
    diagnostics: list[Diagnostic] = []

    # 1. C / C++ family
    for match in _C_FAMILY.finditer(text):
        raw_sev = match.group("severity")
        severity = "warning" if raw_sev == "warning" else ("info" if raw_sev == "note" else "error")
        diagnostics.append(
            Diagnostic(
                severity=severity,
                message=match.group("message").strip(),
                file=match.group("file"),
                line=int(match.group("line")),
                column=int(match.group("column")) if match.group("column") else None,
            )
        )

    if diagnostics:
        return diagnostics

    # 2. Java family
    for match in _JAVA_FAMILY.finditer(text):
        raw_sev = match.group("severity")
        severity = "warning" if raw_sev == "warning" else "error"
        diagnostics.append(
            Diagnostic(
                severity=severity,
                message=match.group("message").strip(),
                file=match.group("file"),
                line=int(match.group("line")),
                column=None,
            )
        )

    if diagnostics:
        return diagnostics

    # 3. Python errors
    if language in ("Python", ""):
        locations = list(_PY_FILE.finditer(text))
        message = None
        for candidate in _PY_MESSAGE.finditer(text):
            message = candidate
        if message:
            column = None
            loc = locations[-1] if locations else None
            if loc:
                lines = text.splitlines()
                try:
                    index = lines.index(next(line for line in lines if loc.group(0) in line))
                    if index + 2 < len(lines) and "^" in lines[index + 2]:
                        column = lines[index + 2].index("^") + 1
                except (StopIteration, ValueError):
                    pass
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    message=f"{message.group('severity')}: {message.group('message')}",
                    file=loc.group("file") if loc else "",
                    line=int(loc.group("line")) if loc else None,
                    column=column,
                )
            )
            return diagnostics

    # 4. JavaScript errors
    if language in ("JavaScript", ""):
        loc_match = _JS_LOCATION.search(text)
        msg_match = _JS_MESSAGE.search(text)
        if loc_match and msg_match:
            column = None
            lines = text.splitlines()
            for i, l in enumerate(lines):
                if "^" in l:
                    column = l.index("^") + 1
                    break
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    message=f"{msg_match.group('severity')}: {msg_match.group('message')}",
                    file=loc_match.group("file"),
                    line=int(loc_match.group("line")),
                    column=column,
                )
            )
            return diagnostics

    return diagnostics


def sql_diagnostic(message: str) -> Diagnostic:
    """Represent SQLite failures consistently with optional line extraction."""
    line = None
    m = re.search(r"at line (\d+)", message, re.IGNORECASE)
    if m:
        line = int(m.group(1))
    return Diagnostic(severity="error", message=message.strip() or "SQL error", line=line)

