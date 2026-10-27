"""Global test safeguards for external-launch APIs."""
from __future__ import annotations

import webbrowser

import pytest


@pytest.fixture(autouse=True)
def browser_launches(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Prevent tests from opening the user's browser and retain launch targets."""
    launches: list[str] = []

    def record(target: object, *args: object, **kwargs: object) -> bool:
        launches.append(str(target))
        return True

    monkeypatch.setattr(webbrowser, "open", record)
    try:
        from PySide6.QtGui import QDesktopServices
    except ImportError:
        pass
    else:
        monkeypatch.setattr(QDesktopServices, "openUrl", record)
    return launches
