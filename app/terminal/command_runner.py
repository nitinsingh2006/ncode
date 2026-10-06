"""
Nitin Editor - terminal/command_runner.py
Execute shell commands on Linux using a controlled subprocess.

Security design:
- Linux mode: uses /bin/bash with the user's command (shell=True is needed
  to support pipelines, redirects, and compound commands that users naturally type).
  shell=True is documented here and used consciously, not accidentally.
- macOS/Windows modes: NOT executed on this Ubuntu machine. The OS is detected
  and informational messages are shown instead. No fabricated output is produced.
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


@dataclass
class CommandResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    elapsed_time: float = 0.0
    timed_out: bool = False
    cancelled: bool = False
    error_message: str = ""
    simulated: bool = False   # True when macOS/Windows mode on a non-matching OS


# Detect the actual host OS once at import time
_HOST_OS = platform.system()  # "Linux", "Darwin", "Windows"


def get_host_os_name() -> str:
    """Return a human-readable host OS string."""
    if _HOST_OS == "Linux":
        return "Linux"
    elif _HOST_OS == "Darwin":
        return "macOS"
    elif _HOST_OS == "Windows":
        return "Windows"
    return _HOST_OS


def is_target_os_available(target_os: str) -> bool:
    """Return True if the target OS matches the actual host OS."""
    mapping = {"Linux": "Linux", "macOS": "Darwin", "Windows": "Windows"}
    return _HOST_OS == mapping.get(target_os, "")


def unavailable_os_message(target_os: str) -> str:
    """
    Return the informational message shown when the target OS is not this machine.
    Nitin Editor never fabricates real command output for unavailable OSes.
    """
    host = get_host_os_name()
    return (
        f"⚠  {target_os} environment is not available on this machine.\n\n"
        f"   This system is running: {host}\n\n"
        f"   {target_os} commands cannot be executed here.\n"
        f"   Use the Command Reference tab to see equivalent commands.\n"
    )


class CommandRunner:
    """
    Execute a shell command in a background-friendly way with streaming output,
    timeout, and stop support.

    Thread-safe methods: stop() can be called from any thread.
    """

    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen] = None
        self._stopped: bool = False
        self._lock = threading.Lock()

    def stop(self) -> None:
        """Terminate the running command. Safe to call from any thread."""
        self._stopped = True
        with self._lock:
            proc = self._process
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    try:
                        proc.wait(timeout=1.5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                except (ProcessLookupError, PermissionError, OSError):
                    pass

    def run(
        self,
        command: str,
        target_os: str = "Linux",
        timeout: int = 30,
        cwd: Optional[str] = None,
        on_stdout: Optional[Callable[[str], None]] = None,
        on_stderr: Optional[Callable[[str], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> CommandResult:
        """
        Execute command string. For Linux (on Linux host), runs it via /bin/bash.
        For macOS/Windows on a Linux host, returns an informational message instead.
        """
        self._stopped = False
        result = CommandResult()

        # ── OS availability check ───────────────────────────────────────────
        if not is_target_os_available(target_os):
            msg = unavailable_os_message(target_os)
            result.simulated = True
            result.error_message = msg
            result.exit_code = -1
            if on_stdout:
                on_stdout(msg)
            return result

        # ── Empty command ───────────────────────────────────────────────────
        cmd_stripped = command.strip()
        if not cmd_stripped:
            result.error_message = "No command entered."
            result.exit_code = 0
            return result

        # ── Execute via /bin/bash ───────────────────────────────────────────
        # shell=True is used intentionally here to support pipelines (|),
        # redirects (>, >>), compound commands (&&, ||, ;), and other shell
        # features that are natural and expected in a terminal emulator.
        # The user has explicit control; dangerous commands are pre-screened.
        env = os.environ.copy()
        env["TERM"] = "dumb"  # Suppress ANSI sequences that garble output

        start = time.monotonic()
        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []

        try:
            proc = subprocess.Popen(
                cmd_stripped,
                shell=True,
                executable="/bin/bash",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd or str(Path.home()),
                env=env,
                bufsize=0,
            )
            with self._lock:
                self._process = proc

            def _reader(stream, chunks, callback):
                if not stream:
                    return
                try:
                    fd = stream.fileno()
                    while True:
                        data = os.read(fd, 1024)
                        if not data:
                            break
                        text = data.decode("utf-8", errors="replace")
                        chunks.append(text)
                        if callback:
                            callback(text)
                except Exception:
                    pass

            t_out = threading.Thread(
                target=_reader, args=(proc.stdout, stdout_chunks, on_stdout), daemon=True
            )
            t_err = threading.Thread(
                target=_reader, args=(proc.stderr, stderr_chunks, on_stderr), daemon=True
            )
            t_out.start()
            t_err.start()

            # Monitoring loop
            while True:
                if proc.poll() is not None:
                    break
                if self._stopped:
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    break
                elapsed = time.monotonic() - start
                if elapsed > timeout:
                    result.timed_out = True
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    break
                time.sleep(0.05)

            t_out.join(timeout=1.0)
            t_err.join(timeout=1.0)

            result.exit_code = proc.returncode if proc.returncode is not None else -1
            result.stdout = "".join(stdout_chunks)
            result.stderr = "".join(stderr_chunks)

        except FileNotFoundError as e:
            result.error_message = f"Shell not found: {e}"
            result.exit_code = -1
        except Exception as e:
            result.error_message = f"Execution error: {e}"
            result.exit_code = -1
        finally:
            with self._lock:
                self._process = None

        if self._stopped and not result.timed_out:
            result.cancelled = True

        result.elapsed_time = time.monotonic() - start
        return result
