"""Host platform facts and small cross-platform execution contracts."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class HostPlatform(str, Enum):
    LINUX = "Linux"
    WINDOWS = "Windows"
    MACOS = "macOS"
    ANDROID = "Android"
    UNKNOWN = "Unknown"


def detect_host_platform(system_name: str | None = None) -> HostPlatform:
    """Map Python/Java-style host identifiers without inventing a target OS."""
    # Do not import the standard-library ``platform`` module here.  When the
    # editor is launched as ``app/main.py``, its ``app`` directory is also on
    # sys.path and the project's ``app/platform`` package can otherwise shadow
    # that stdlib module.  ``sys.platform`` provides all host facts needed by
    # this small, dependency-free core module.
    if system_name is None:
        if hasattr(sys, "getandroidapilevel"):
            system_name = "Android"
        elif sys.platform.startswith("linux"):
            system_name = "Linux"
        elif sys.platform == "darwin":
            system_name = "Darwin"
        elif sys.platform.startswith(("win", "cygwin")):
            system_name = "Windows"
        else:
            system_name = sys.platform
    system_name = system_name.strip()
    if system_name == "Linux":
        # Android's Python embeddings commonly report Linux; callers on Android
        # should explicitly provide Android rather than treating it as a desktop.
        return HostPlatform.LINUX
    if system_name in {"Darwin", "macOS"}:
        return HostPlatform.MACOS
    if system_name == "Windows":
        return HostPlatform.WINDOWS
    if system_name == "Android":
        return HostPlatform.ANDROID
    return HostPlatform.UNKNOWN


@dataclass(frozen=True)
class ExecutionCapability:
    available: bool
    message: str = ""


class CodeExecutor(Protocol):
    """Contract implemented by desktop runners and Android-safe executors."""
    def capability(self, language: str) -> ExecutionCapability: ...


class TerminalBackend(Protocol):
    """A terminal backend only exposes commands its platform can genuinely run."""
    platform: HostPlatform


class FileSystemProvider(Protocol):
    """Platform file access; Android implementations use document URIs/SAF."""
    def read_text(self, location: str) -> str: ...
    def write_text(self, location: str, content: str) -> None: ...


class DatabaseProvider(Protocol):
    """Local database provider abstraction (SQLite on current clients)."""
    def execute(self, statement: str): ...
