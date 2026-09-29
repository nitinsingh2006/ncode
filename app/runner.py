"""
Nitin Editor - runner.py
Background thread that executes code, streams output in real-time, and handles interactive stdin.
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
      - stdout_signal(str): real-time stdout chunks
      - stderr_signal(str): real-time stderr chunks
      - status_signal(str): execution status updates
      - finished_signal(RunResult): when execution completes (always emitted)

    Thread safety:
      - send_stdin(data) can be called from main thread to send input
      - close_stdin() can be called from main thread to send EOF
      - stop_execution() can be called from main thread to terminate process
    """
    started_signal = Signal()
    stdout_signal = Signal(str)
    stderr_signal = Signal(str)
    status_signal = Signal(str)
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
        """Configure execution options before calling start()."""
        self._language = language
        self._code = code
        self._stdin = stdin_data
        self._timeout = timeout
        self._saved_path = saved_path

    def run(self) -> None:
        """Execute in background thread. Do not call directly — use start()."""
        self.started_signal.emit()
        try:
            result = self._runner.run(
                language=self._language,
                code=self._code,
                stdin_data=self._stdin,
                timeout=self._timeout,
                saved_path=self._saved_path,
                on_stdout=lambda text: self.stdout_signal.emit(text),
                on_stderr=lambda text: self.stderr_signal.emit(text),
                on_status=lambda msg: self.status_signal.emit(msg),
            )
        except Exception as e:
            result = RunResult(
                error_message=f"Unexpected runner error: {e}",
                exit_code=-1,
            )
        self.finished_signal.emit(result)

    def send_stdin(self, data: str) -> bool:
        """Send input string to the live process stdin pipe. Safe to call from main thread."""
        return self._runner.write_stdin(data)

    def close_stdin(self) -> None:
        """Close live stdin pipe (EOF). Safe to call from main thread."""
        self._runner.close_stdin()

    def stop_execution(self) -> None:
        """Request running process to stop. Safe to call from main thread."""
        self._runner.stop()
