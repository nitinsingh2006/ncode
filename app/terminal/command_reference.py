"""
Nitin Editor - terminal/command_reference.py
Cross-platform command equivalence reference for educational use.

This module provides static reference data only — no command execution happens here.
"""
from __future__ import annotations


# Each entry: (description, linux_cmd, macos_cmd, windows_cmd)
COMMAND_REFERENCE: list[tuple[str, str, str, str]] = [
    ("List files",              "ls",           "ls",           "dir"),
    ("List all files (hidden)", "ls -la",        "ls -la",       "dir /a"),
    ("Current directory",       "pwd",           "pwd",          "cd"),
    ("Change directory",        "cd <dir>",      "cd <dir>",     "cd <dir>"),
    ("Create directory",        "mkdir <dir>",   "mkdir <dir>",  "mkdir <dir>"),
    ("Remove empty directory",  "rmdir <dir>",   "rmdir <dir>",  "rmdir <dir>"),
    ("Remove file",             "rm <file>",     "rm <file>",    "del <file>"),
    ("Copy file",               "cp src dst",    "cp src dst",   "copy src dst"),
    ("Move/rename file",        "mv src dst",    "mv src dst",   "move src dst"),
    ("Print text",              "echo Hello",    "echo Hello",   "echo Hello"),
    ("Clear terminal",          "clear",         "clear",        "cls"),
    ("Current user",            "whoami",        "whoami",       "whoami"),
    ("System info",             "uname -a",      "uname -a",     "systeminfo"),
    ("OS version",              "cat /etc/os-release", "sw_vers", "winver"),
    ("Running processes",       "ps aux",        "ps aux",       "tasklist"),
    ("Kill process by PID",     "kill <pid>",    "kill <pid>",   "taskkill /PID <pid>"),
    ("Network configuration",   "ip addr",       "ifconfig",     "ipconfig"),
    ("Network connections",     "ss -tulnp",     "netstat -an",  "netstat -an"),
    ("Ping host",               "ping -c 4 <h>", "ping -c 4 <h>","ping <h>"),
    ("Download URL",            "curl -O <url>", "curl -O <url>","curl -O <url>"),
    ("Show file contents",      "cat <file>",    "cat <file>",   "type <file>"),
    ("Edit file (terminal)",    "nano <file>",   "nano <file>",  "notepad <file>"),
    ("Find files",              "find . -name x","find . -name x","where x"),
    ("Search in files",         "grep pat file", "grep pat file","findstr pat file"),
    ("Disk usage",              "df -h",         "df -h",        "wmic logicaldisk"),
    ("Free memory",             "free -h",       "vm_stat",      "systeminfo | findstr Memory"),
    ("Environment variables",   "env",           "env",          "set"),
    ("Set env variable",        "export V=val",  "export V=val", "set V=val"),
    ("Run script",              "bash script.sh","bash script.sh","script.bat"),
    ("Python interpreter",      "python3",       "python3",      "python"),
    ("Install package (pip)",   "pip3 install x","pip3 install x","pip install x"),
    ("SSH to host",             "ssh user@host", "ssh user@host","ssh user@host"),
    ("Archive files",           "tar -czf a.tgz","tar -czf a.tgz","Compress-Archive"),
    ("Shutdown",                "sudo shutdown -h now","sudo shutdown -h now","shutdown /s /t 0"),
    ("Restart",                 "sudo reboot",   "sudo reboot",  "shutdown /r /t 0"),
]


def get_reference_text() -> str:
    """
    Return the full command reference as a formatted string.
    """
    col_w = [30, 25, 25, 30]
    header = ("Operation", "Linux", "macOS", "Windows")

    def _row(cells: tuple[str, ...]) -> str:
        return "  ".join(f"{c:<{col_w[i]}}" for i, c in enumerate(cells))

    sep = "  ".join("-" * w for w in col_w)
    lines = [
        "Cross-Platform Command Reference",
        "=" * 80,
        _row(header),
        sep,
    ]
    for desc, linux, mac, win in COMMAND_REFERENCE:
        lines.append(_row((desc, linux, mac, win)))

    lines.append("")
    lines.append("Note: Commands marked with sudo require administrator/root privileges.")
    lines.append("      <dir>, <file>, <url>, <h>, <pid>, <v>, x = placeholders.")
    return "\n".join(lines)


def lookup_equivalents(command: str) -> str | None:
    """
    Given a Linux/macOS/Windows command, find its cross-platform equivalents.
    Returns a formatted string or None if not found.
    """
    cmd_lower = command.strip().lower().split()[0] if command.strip() else ""
    if not cmd_lower:
        return None

    results: list[str] = []
    for desc, linux, mac, win in COMMAND_REFERENCE:
        candidates = {linux.split()[0], mac.split()[0], win.split()[0]}
        if cmd_lower in candidates:
            results.append(
                f"  {desc}:\n"
                f"    Linux:   {linux}\n"
                f"    macOS:   {mac}\n"
                f"    Windows: {win}"
            )

    if not results:
        return None
    return "Cross-platform equivalents:\n\n" + "\n\n".join(results)
