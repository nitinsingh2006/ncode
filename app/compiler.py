"""
Nitin Editor - compiler.py
Language detection, compilation, and execution logic.

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
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ── Language definitions ────────────────────────────────────────────────────

EXTENSION_MAP: dict[str, str] = {
    ".py": "Python",
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".java": "Java",
    ".js": "JavaScript",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
}

LANGUAGES: list[str] = ["Python", "C", "C++", "Java", "JavaScript", "HTML", "CSS"]

LANGUAGE_EXTENSIONS: dict[str, str] = {
    "Python": ".py",
    "C": ".c",
    "C++": ".cpp",
    "Java": ".java",
    "JavaScript": ".js",
    "HTML": ".html",
    "CSS": ".css",
}

# Max bytes captured from stdout/stderr to prevent memory exhaustion
MAX_OUTPUT_BYTES = 1 * 1024 * 1024  # 1 MB


def detect_language(file_path: str | Path) -> Optional[str]:
    """Detect language from file extension."""
    ext = Path(file_path).suffix.lower()
    return EXTENSION_MAP.get(ext)


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
    # Distinguish compile errors from runtime errors
    is_compile_error: bool = False


# ── Runner ──────────────────────────────────────────────────────────────────

class CodeRunner:
    """
    Handles compilation and execution of code in a subprocess.
    Thread-safe stop() can be called from another thread.
    """

    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen] = None
        self._temp_dir: Optional[Path] = None
        self._stopped: bool = False

    def stop(self) -> None:
        """Terminate the running process. Safe to call from any thread."""
        self._stopped = True
        proc = self._process
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            except (ProcessLookupError, PermissionError):
                pass  # Process already gone

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
    ) -> RunResult:
        """
        Execute the given code in the given language.
        Returns a RunResult with stdout, stderr, exit_code, and timing.

        stdin_data is passed to the subprocess via communicate(input=...).
        This correctly handles: C scanf, C++ cin, Python input(), Java Scanner,
        Node.js process.stdin — all receive the data atomically at start.
        """
        self._stopped = False
        result = RunResult()

        # Check required tools
        missing = get_missing_tools(language)
        if missing:
            result.error_message = (
                f"Required tool(s) not found: {', '.join(missing)}\n"
                f"{_install_hint(language)}"
            )
            result.exit_code = -1
            return result

        # HTML/CSS are not executed — they are previewed
        if language in ("HTML", "CSS"):
            result.error_message = "PREVIEW"
            return result

        temp_dir = self._make_temp_dir()
        try:
            compile_cmd, run_cmd = _build_commands(language, code, temp_dir, saved_path)

            # Compilation step (C, C++, Java)
            if compile_cmd:
                compile_result = _run_subprocess(
                    compile_cmd,
                    stdin_data="",
                    timeout=max(timeout, 30),  # Give compiler at least 30s
                    cwd=temp_dir,
                    process_ref=self,
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

            if not run_cmd:
                result.error_message = "Internal error: no run command built."
                result.exit_code = -1
                return result

            if self._stopped:
                result.cancelled = True
                return result

            # Execution step — pass stdin_data to the program
            exec_result = _run_subprocess(
                run_cmd,
                stdin_data=stdin_data,
                timeout=timeout,
                cwd=temp_dir,
                process_ref=self,
            )
            result = exec_result
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
    """
    Build (compile_cmd, run_cmd) for the given language.
    Returns (None, run_cmd) for interpreted languages,
    (compile_cmd, run_cmd) for compiled languages.
    """
    compile_cmd: Optional[list[str]] = None
    run_cmd: Optional[list[str]] = None

    if language == "Python":
        src = temp_dir / "script.py"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["python3", "-u", str(src)]  # -u = unbuffered

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
    """Extract the public class name from Java source code."""
    import re
    # public class Name
    m = re.search(r'\bpublic\s+class\s+(\w+)', code)
    if m:
        return m.group(1)
    # fallback: any class Name
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
) -> RunResult:
    """
    Run a command as a subprocess and capture output.

    stdin_data is encoded to UTF-8 and passed to the process via communicate().
    This is the standard batch-stdin approach — correct for programs using
    scanf, cin, input(), Scanner, process.stdin.read(), etc.

    Note: communicate() sends ALL stdin at once then reads all output.
    This is correct for competitive-programming-style programs. For fully
    interactive programs (prompts after each input line), a Popen+pty approach
    would be needed — not implemented here since it requires OS-specific code.
    """
    result = RunResult()
    start_time = time.monotonic()

    # Build environment — include common binary paths
    env = os.environ.copy()
    path_extra = "/usr/local/bin:/usr/bin:/bin"
    current_path = env.get("PATH", "")
    if path_extra not in current_path:
        env["PATH"] = path_extra + ":" + current_path

    # Prepare stdin bytes
    stdin_bytes = stdin_data.encode("utf-8") if stdin_data else b""

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd) if cwd else None,
            env=env,
            # No shell=True — security: cmd is always a list
        )
        if process_ref is not None:
            process_ref._process = proc

        try:
            stdout_bytes, stderr_bytes = proc.communicate(
                input=stdin_bytes,
                timeout=timeout,
            )
            # Truncate large output
            stdout_bytes = stdout_bytes[:MAX_OUTPUT_BYTES]
            stderr_bytes = stderr_bytes[:MAX_OUTPUT_BYTES]
            result.stdout = stdout_bytes.decode("utf-8", errors="replace")
            result.stderr = stderr_bytes.decode("utf-8", errors="replace")
            result.exit_code = proc.returncode

        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                stdout_bytes, stderr_bytes = proc.communicate(timeout=2)
            except Exception:
                stdout_bytes, stderr_bytes = b"", b""
            result.stdout = stdout_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
            result.stderr = stderr_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="replace")
            result.timed_out = True
            result.exit_code = -1

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
            process_ref._process = None

    result.elapsed_time = time.monotonic() - start_time
    return result
