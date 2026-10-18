"""
Nitin Editor - compiler.py
Language detection, compilation, and execution logic with real-time streaming and interactive stdin.

Security notes:
- No shell=True usage
- subprocess.Popen with list arguments only
- Temp dirs isolated per run, cleaned after execution
- Processes killed on timeout or STOP
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from app.core.languages import EXTENSION_MAP, LANGUAGES, LANGUAGE_EXTENSIONS, detect_language

# ── Language definitions ────────────────────────────────────────────────────

# Terminal/command environment entries (separate from programming languages)
TERMINAL_ENVS: list[str] = ["Linux Terminal", "macOS Terminal", "Windows Terminal"]

# Max bytes captured from stdout/stderr to prevent memory exhaustion
MAX_OUTPUT_BYTES = 1 * 1024 * 1024  # 1 MB


# ── Dependency checking ─────────────────────────────────────────────────────

def check_tool(tool: str) -> bool:
    """Return True if the given tool is available in PATH."""
    return shutil.which(tool) is not None


def get_missing_tools(language: str) -> list[str]:
    """Return list of missing tools required for the given language."""
    missing: list[str] = []
    if language == "Python":
        if not check_tool("python3"):
            missing.append("python3")
    elif language == "C":
        if not check_tool("gcc"):
            missing.append("gcc")
    elif language == "C++":
        if not check_tool("g++"):
            missing.append("g++")
    elif language == "Java":
        if not check_tool("javac"):
            missing.append("javac")
        if not check_tool("java"):
            missing.append("java")
    elif language == "JavaScript":
        if not check_tool("node"):
            missing.append("node")
    # SQL uses Python's built-in sqlite3 — always available with Python 3
    # Terminal environments are handled by CommandRunner, not compiler
    return missing


def _install_hint(language: str) -> str:
    hints: dict[str, str] = {
        "Python": "Install: sudo apt-get install python3",
        "C": "Install: sudo apt-get install gcc",
        "C++": "Install: sudo apt-get install g++",
        "Java": "Install: sudo apt-get install openjdk-21-jdk",
        "JavaScript": "Install: sudo apt-get install nodejs",
    }
    return hints.get(language, "Please install the required compiler/runtime.")


# ── Run result ──────────────────────────────────────────────────────────────

@dataclass
class RunResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    elapsed_time: float = 0.0
    timed_out: bool = False
    cancelled: bool = False
    error_message: str = ""
    is_compile_error: bool = False
    compiler_output: str = ""


# ── Runner ──────────────────────────────────────────────────────────────────

class CodeRunner:
    """
    Handles compilation and execution of code in a subprocess.
    Thread-safe methods write_stdin(), close_stdin(), and stop() can be called from any thread.
    """

    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen] = None
        self._temp_dir: Optional[Path] = None
        self._stopped: bool = False
        self._stdin_ready: bool = False
        self._lock = threading.Lock()

    def stop(self) -> None:
        """Terminate the running process. Safe to call from any thread."""
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

    def write_stdin(self, data: str) -> bool:
        """Write string data into live stdin pipe of running process."""
        with self._lock:
            proc = self._process
            if self._stdin_ready and proc and proc.stdin and not proc.stdin.closed and proc.poll() is None:
                try:
                    proc.stdin.write(data.encode("utf-8"))
                    proc.stdin.flush()
                    return True
                except (BrokenPipeError, OSError):
                    pass
        return False

    def close_stdin(self) -> None:
        """Send EOF to live stdin pipe."""
        with self._lock:
            proc = self._process
            if self._stdin_ready and proc and proc.stdin and not proc.stdin.closed:
                try:
                    proc.stdin.close()
                except (BrokenPipeError, OSError):
                    pass

    def is_waiting_for_stdin(self) -> bool:
        """
        Return True if the running process is blocked waiting for stdin input.
        Thread-safe method.
        """
        with self._lock:
            proc = self._process
            if not proc or proc.poll() is not None:
                return False
            pid = proc.pid

        try:
            wchan_path = Path(f"/proc/{pid}/wchan")
            if wchan_path.exists():
                wchan = wchan_path.read_text(encoding="utf-8", errors="ignore").strip()
                # Match stdin read syscalls (e.g. anon_pipe_read, n_tty_read, sys_read, read_chan)
                if any(term in wchan for term in ("read", "pipe", "tty")):
                    if not any(ex in wchan for ex in ("sleep", "futex", "poll")):
                        return True
                return False
        except Exception:
            pass
        return False

    def _make_temp_dir(self) -> Path:
        """Create an isolated temp directory for this run."""
        temp = Path(tempfile.mkdtemp(prefix="ncode_"))
        self._temp_dir = temp
        return temp

    def _cleanup_temp(self) -> None:
        if self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None

    def run(
        self,
        language: str,
        code: str,
        stdin_data: str = "",
        timeout: int = 10,
        saved_path: Optional[Path] = None,
        on_stdout: Optional[Callable[[str], None]] = None,
        on_stderr: Optional[Callable[[str], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> RunResult:
        """
        Execute code in specified language with real-time streaming and interactive stdin.
        """
        self._stopped = False
        result = RunResult()

        missing = get_missing_tools(language)
        if missing:
            result.error_message = (
                f"Required tool(s) not found: {', '.join(missing)}\n"
                f"{_install_hint(language)}"
            )
            result.exit_code = -1
            return result

        if language in ("HTML", "CSS"):
            result.error_message = "PREVIEW"
            return result

        temp_dir = self._make_temp_dir()
        try:
            compile_cmd, run_cmd = _build_commands(language, code, temp_dir, saved_path)

            if compile_cmd:
                if on_status:
                    on_status("Compiling…")
                compile_result = _run_subprocess(
                    compile_cmd,
                    stdin_data="",
                    timeout=max(timeout, 30),
                    cwd=temp_dir,
                    process_ref=self,
                    allow_stdin=False,
                )
                if self._stopped:
                    result.cancelled = True
                    return result
                if compile_result.exit_code != 0:
                    result.stderr = compile_result.stderr
                    result.stdout = compile_result.stdout
                    result.exit_code = compile_result.exit_code
                    result.elapsed_time = compile_result.elapsed_time
                    result.is_compile_error = True
                    return result
                # Warnings are valuable diagnostics even when compilation
                # succeeds.  Stream them immediately and retain them for the
                # Problems panel after the program exits.
                compiler_output = compile_result.stderr
                if compiler_output and on_stderr:
                    on_stderr(compiler_output)
            else:
                compiler_output = ""

            if not run_cmd:
                result.error_message = "Internal error: no run command built."
                result.exit_code = -1
                return result

            if self._stopped:
                result.cancelled = True
                return result

            exec_result = _run_subprocess(
                run_cmd,
                stdin_data=stdin_data,
                timeout=timeout,
                cwd=temp_dir,
                process_ref=self,
                on_stdout=on_stdout,
                on_stderr=on_stderr,
                on_status=on_status,
                allow_stdin=True,
            )
            result = exec_result
            result.compiler_output = compiler_output
            if self._stopped and not result.timed_out:
                result.cancelled = True

        finally:
            self._cleanup_temp()

        return result


def _build_commands(
    language: str,
    code: str,
    temp_dir: Path,
    saved_path: Optional[Path],
) -> tuple[Optional[list[str]], Optional[list[str]]]:

    compile_cmd: Optional[list[str]] = None
    run_cmd: Optional[list[str]] = None

    if language == "Python":
        src = temp_dir / "script.py"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["python3", "-u", str(src)]

    elif language == "C":
        src = temp_dir / "main.c"
        src.write_text(code, encoding="utf-8")
        out = temp_dir / "main_c"
        compile_cmd = ["gcc", str(src), "-o", str(out), "-lm", "-Wall"]
        run_cmd = [str(out)]

    elif language == "C++":
        src = temp_dir / "main.cpp"
        src.write_text(code, encoding="utf-8")
        out = temp_dir / "main_cpp"
        compile_cmd = ["g++", str(src), "-o", str(out), "-std=c++17", "-Wall"]
        run_cmd = [str(out)]

    elif language == "Java":
        class_name = _extract_java_class_name(code) or "Main"
        src = temp_dir / f"{class_name}.java"
        src.write_text(code, encoding="utf-8")
        compile_cmd = ["javac", "-encoding", "UTF-8", str(src)]
        run_cmd = ["java", "-cp", str(temp_dir), class_name]

    elif language == "JavaScript":
        src = temp_dir / "script.js"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["node", str(src)]

    return compile_cmd, run_cmd


def _extract_java_class_name(code: str) -> Optional[str]:
    import re
    m = re.search(r'\bpublic\s+class\s+(\w+)', code)
    if m:
        return m.group(1)
    m = re.search(r'\bclass\s+(\w+)', code)
    if m:
        return m.group(1)
    return None


def _run_subprocess(
    cmd: list[str],
    stdin_data: str = "",
    timeout: int = 10,
    cwd: Optional[Path] = None,
    process_ref: Optional[CodeRunner] = None,
    on_stdout: Optional[Callable[[str], None]] = None,
    on_stderr: Optional[Callable[[str], None]] = None,
    on_status: Optional[Callable[[str], None]] = None,
    allow_stdin: bool = False,
) -> RunResult:
    """
    Run command as subprocess with live streaming of stdout/stderr and open stdin.
    """
    result = RunResult()
    start_time = time.monotonic()

    env = os.environ.copy()
    path_extra = "/usr/local/bin:/usr/bin:/bin"
    current_path = env.get("PATH", "")
    if path_extra not in current_path:
        env["PATH"] = path_extra + ":" + current_path
    env["PYTHONUNBUFFERED"] = "1"

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd) if cwd else None,
            env=env,
            bufsize=0,
        )
        if process_ref is not None:
            with process_ref._lock:
                process_ref._process = proc
                process_ref._stdin_ready = allow_stdin

        if allow_stdin and on_status:
            on_status("Running…")

        # Write preloaded stdin data if present without closing stdin
        if stdin_data and proc.stdin:
            try:
                data_to_write = stdin_data if stdin_data.endswith("\n") else stdin_data + "\n"
                proc.stdin.write(data_to_write.encode("utf-8"))
                proc.stdin.flush()
            except (BrokenPipeError, OSError):
                pass

        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []

        def _reader(stream, chunks_list, callback):
            if not stream:
                return
            try:
                fd = stream.fileno()
                while True:
                    data = os.read(fd, 1024)
                    if not data:
                        break
                    text = data.decode("utf-8", errors="replace")
                    chunks_list.append(text)
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

        # Monitoring loop with interactive-aware timeout
        active_compute_duration: float = 0.0
        last_tick = time.monotonic()

        while True:
            poll_ret = proc.poll()
            if poll_ret is not None:
                break

            if process_ref and process_ref._stopped:
                try:
                    proc.terminate()
                    try:
                        proc.wait(timeout=1.5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                except Exception:
                    pass
                break

            now = time.monotonic()
            dt = now - last_tick
            last_tick = now

            if allow_stdin and process_ref:
                is_waiting = process_ref.is_waiting_for_stdin()
                if is_waiting:
                    # Reset active computation timer while waiting for user input
                    active_compute_duration = 0.0
                else:
                    active_compute_duration += dt
                    if active_compute_duration > timeout:
                        result.timed_out = True
                        try:
                            proc.kill()
                            proc.wait()
                        except Exception:
                            pass
                        break
            else:
                active_compute_duration += dt
                if active_compute_duration > timeout:
                    result.timed_out = True
                    try:
                        proc.kill()
                        proc.wait()
                    except Exception:
                        pass
                    break

            time.sleep(0.05)

        t_out.join(timeout=1.0)
        t_err.join(timeout=1.0)

        # Safely close stdin if open
        if proc.stdin and not proc.stdin.closed:
            try:
                proc.stdin.close()
            except Exception:
                pass

        result.exit_code = proc.returncode if proc.returncode is not None else -1
        result.stdout = "".join(stdout_chunks)[:MAX_OUTPUT_BYTES]
        result.stderr = "".join(stderr_chunks)[:MAX_OUTPUT_BYTES]

    except FileNotFoundError as e:
        result.error_message = f"Command not found: {cmd[0]}\n{e}"
        result.exit_code = -1
    except PermissionError as e:
        result.error_message = f"Permission denied running: {cmd[0]}\n{e}"
        result.exit_code = -1
    except Exception as e:
        result.error_message = f"Execution error: {e}"
        result.exit_code = -1
    finally:
        if process_ref is not None:
            with process_ref._lock:
                process_ref._process = None
                process_ref._stdin_ready = False

    result.elapsed_time = time.monotonic() - start_time
    return result
