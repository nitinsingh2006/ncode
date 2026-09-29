"""
Nitin Editor - runner.py
Background thread that executes code and emits signals with results.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from .compiler import CodeRunner, RunResult


class RunnerThread(QThread):
    """
    Runs code in a background QThread so the UI stays responsive.
    Emits:
      - started_signal: when execution begins
      - finished_signal(RunResult): when execution completes
      - output_chunk(str): for streaming output (future enhancement)
    """
    started_signal = Signal()
    finished_signal = Signal(object)  # RunResult

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._runner = CodeRunner()
        self._language: str = ""
        self._code: str = ""
        self._stdin: str = ""
        self._timeout: int = 10
        self._saved_path: Optional[Path] = None

    def configure(
        self,
        language: str,
        code: str,
        stdin_data: str = "",
        timeout: int = 10,
        saved_path: Optional[Path] = None,
    ) -> None:
        self._language = language
        self._code = code
        self._stdin = stdin_data
        self._timeout = timeout
        self._saved_path = saved_path

    def run(self) -> None:
        self.started_signal.emit()
        result = self._runner.run(
            language=self._language,
            code=self._code,
            stdin_data=self._stdin,
            timeout=self._timeout,
            saved_path=self._saved_path,
        )
        self.finished_signal.emit(result)

    def stop_execution(self) -> None:
        self._runner.stop()
