"""
Nitin Editor - terminal/safety.py
Dangerous command detection for the integrated terminal.

Detects potentially destructive commands and requires explicit user confirmation
before executing them. Does NOT silently block — the user remains in control.
"""
from __future__ import annotations

import re
from typing import NamedTuple


class DangerResult(NamedTuple):
    is_dangerous: bool
    reason: str


# Patterns that indicate high-risk operations (Linux/macOS)
_LINUX_DANGER_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"rm\s+.*(-[a-zA-Z]*f[a-zA-Z]*r|--recursive.*--force|-rf|-fr)\s*/", re.IGNORECASE),
        "Recursive forced deletion of root filesystem (rm -rf /)",
    ),
    (
        re.compile(r"rm\s+.*-[a-zA-Z]*f[a-zA-Z]*\s+/", re.IGNORECASE),
        "Forced deletion from root (rm -f /...)",
    ),
    (
        re.compile(r"\bmkfs\b", re.IGNORECASE),
        "mkfs formats a filesystem — permanently erases all data on the target device",
    ),
    (
        re.compile(r"\bdd\b.*\bif=", re.IGNORECASE),
        "dd can overwrite disks and destroy data — check source/destination carefully",
    ),
    (
        re.compile(r"\bshutdown\b", re.IGNORECASE),
        "shutdown will power off or restart the system",
    ),
    (
        re.compile(r"\breboot\b", re.IGNORECASE),
        "reboot will restart the system",
    ),
    (
        re.compile(r"\bpoweroff\b", re.IGNORECASE),
        "poweroff will shut down the system",
    ),
    (
        re.compile(r"\bhalt\b", re.IGNORECASE),
        "halt will stop the system",
    ),
    (
        re.compile(r"\bchmod\s+-R\s+777\b", re.IGNORECASE),
        "chmod -R 777 removes all permission restrictions recursively",
    ),
    (
        re.compile(r">\s*/dev/(s|h|v)d[a-z]", re.IGNORECASE),
        "Redirect output directly to a disk device — this can destroy the disk",
    ),
    (
        re.compile(r"\bwipefs\b", re.IGNORECASE),
        "wipefs erases filesystem signatures from devices",
    ),
    (
        re.compile(r"\bfdisk\b", re.IGNORECASE),
        "fdisk modifies disk partition tables",
    ),
    (
        re.compile(r"\bparted\b", re.IGNORECASE),
        "parted modifies disk partition tables",
    ),
]

# Windows equivalent dangerous commands
_WINDOWS_DANGER_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\bformat\s+[a-zA-Z]:", re.IGNORECASE),
        "format will erase all data on the specified drive",
    ),
    (
        re.compile(r"\bdiskpart\b", re.IGNORECASE),
        "diskpart modifies disk partitions — can destroy data",
    ),
    (
        re.compile(r"rd\s+/s\s+/q\s+[a-zA-Z]:\\", re.IGNORECASE),
        "rd /s /q recursively deletes a directory tree",
    ),
    (
        re.compile(r"\bshutdown\b.*(/s|/r|/h)", re.IGNORECASE),
        "shutdown will shut down or restart the system",
    ),
]


def check_command(command: str, target_os: str = "Linux") -> DangerResult:
    """
    Analyse a command string for dangerous operations.

    Args:
        command: The raw command string as typed by the user.
        target_os: "Linux", "macOS", or "Windows".

    Returns:
        DangerResult with is_dangerous flag and a human-readable reason.
    """
    if not command.strip():
        return DangerResult(False, "")

    patterns = _LINUX_DANGER_PATTERNS if target_os != "Windows" else _WINDOWS_DANGER_PATTERNS

    for pattern, reason in patterns:
        if pattern.search(command):
            return DangerResult(True, reason)

    return DangerResult(False, "")


def warning_message(command: str, reason: str) -> str:
    """Build the warning dialog message."""
    return (
        f"⚠  WARNING — Potentially Dangerous Command\n\n"
        f"Command:  {command}\n\n"
        f"Risk:  {reason}\n\n"
        f"This command could seriously damage your system.\n"
        f"Make absolutely sure you know what this does before proceeding."
    )
