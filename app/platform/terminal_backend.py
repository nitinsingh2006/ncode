"""Actual-host terminal selection; no cross-OS command simulation."""
from __future__ import annotations

from dataclasses import dataclass

from app.core.platform import HostPlatform, detect_host_platform


@dataclass(frozen=True)
class DesktopTerminalBackend:
    platform: HostPlatform

    @property
    def shell(self) -> str:
        if self.platform == HostPlatform.WINDOWS:
            return "cmd.exe"
        return "/bin/zsh" if self.platform == HostPlatform.MACOS else "/bin/bash"

    @property
    def is_shell_command(self) -> bool:
        return self.platform != HostPlatform.WINDOWS


@dataclass(frozen=True)
class AndroidTerminalBackend:
    platform: HostPlatform = HostPlatform.ANDROID

    def availability_message(self) -> str:
        return "Android Terminal supports only app-provided sandbox operations; no unrestricted host shell is available."


def select_terminal_backend(system_name: str | None = None):
    host = detect_host_platform(system_name)
    if host == HostPlatform.ANDROID:
        return AndroidTerminalBackend()
    return DesktopTerminalBackend(host)
