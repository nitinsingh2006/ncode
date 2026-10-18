"""Platform implementations. Desktop code imports these through stable contracts."""

from .terminal_backend import DesktopTerminalBackend, AndroidTerminalBackend, select_terminal_backend

__all__ = ["DesktopTerminalBackend", "AndroidTerminalBackend", "select_terminal_backend"]
