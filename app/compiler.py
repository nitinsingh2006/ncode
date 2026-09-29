"""
Nitin Editor - compiler.py
Language detection, compilation, and execution logic.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
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


def detect_language(file_path: str | Path) -> Optional[str]:
    """Detect language from file extension."""
    ext = Path(file_path).suffix.lower()
    return EXTENSION_MAP.get(ext)


# ── Dependency checking ─────────────────────────────────────────────────────

def check_tool(tool: str) -> bool:
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


# ── Runner ──────────────────────────────────────────────────────────────────

class CodeRunner:
    """Handles compilation and execution of code in a subprocess."""

    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen] = None
        self._temp_dir: Optional[Path] = None

    def stop(self) -> None:
        """Terminate the running process."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()

    def _make_temp_dir(self) -> Path:
        """Create an isolated temp directory for this run."""
        temp = Path(tempfile.mkdtemp(prefix="ncode_"))
        self._temp_dir = temp
        return temp

    def _cleanup_temp(self) -> None:
        if self._temp_dir and self._temp_dir.exists():
            import shutil as sh
            sh.rmtree(self._temp_dir, ignore_errors=True)
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
        """
        result = RunResult()

        # Check tools
        missing = get_missing_tools(language)
        if missing:
            tool_names = ", ".join(missing)
            install_hint = _install_hint(language)
            result.error_message = (
                f"Required tool(s) not found: {tool_names}\n{install_hint}"
            )
            result.exit_code = -1
            return result

        # HTML/CSS are handled specially (no subprocess execution)
        if language in ("HTML", "CSS"):
            result.error_message = "PREVIEW"
            return result

        temp_dir = self._make_temp_dir()
        try:
            cmd, compile_cmd = _build_commands(
                language, code, temp_dir, saved_path
            )

            # Compilation step (C, C++, Java)
            if compile_cmd:
                compile_result = _run_subprocess(
                    compile_cmd, stdin_data="", timeout=timeout
                )
                if compile_result.exit_code != 0:
                    result.stderr = compile_result.stderr
                    result.stdout = compile_result.stdout
                    result.exit_code = compile_result.exit_code
                    result.elapsed_time = compile_result.elapsed_time
                    return result

            if not cmd:
                result.error_message = "Internal error: no run command built."
                result.exit_code = -1
                return result

            # Execution step
            exec_result = _run_subprocess(
                cmd,
                stdin_data=stdin_data,
                timeout=timeout,
                cwd=temp_dir,
                process_ref=self,
            )
            result = exec_result
        finally:
            self._cleanup_temp()

        return result


def _install_hint(language: str) -> str:
    hints: dict[str, str] = {
        "Python": "Install with: sudo apt-get install python3",
        "C": "Install with: sudo apt-get install gcc",
        "C++": "Install with: sudo apt-get install g++",
        "Java": "Install with: sudo apt-get install openjdk-21-jdk",
        "JavaScript": "Install with: sudo apt-get install nodejs",
    }
    return hints.get(language, "Please install the required compiler/runtime.")


def _build_commands(
    language: str,
    code: str,
    temp_dir: Path,
    saved_path: Optional[Path],
) -> tuple[Optional[list[str]], Optional[list[str]]]:
    """
    Build (run_cmd, compile_cmd) for the given language.
    Returns (run_cmd, None) for interpreted languages,
    (run_cmd, compile_cmd) for compiled languages.
    """
    compile_cmd: Optional[list[str]] = None
    run_cmd: Optional[list[str]] = None

    if language == "Python":
        src = temp_dir / "script.py"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["python3", str(src)]

    elif language == "C":
        src = temp_dir / "main.c"
        src.write_text(code, encoding="utf-8")
        out = temp_dir / "main_c"
        compile_cmd = ["gcc", str(src), "-o", str(out), "-lm"]
        run_cmd = [str(out)]

    elif language == "C++":
        src = temp_dir / "main.cpp"
        src.write_text(code, encoding="utf-8")
        out = temp_dir / "main_cpp"
        compile_cmd = ["g++", str(src), "-o", str(out), "-std=c++17"]
        run_cmd = [str(out)]

    elif language == "Java":
        # Extract public class name from code
        class_name = _extract_java_class_name(code) or "Main"
        src = temp_dir / f"{class_name}.java"
        src.write_text(code, encoding="utf-8")
        compile_cmd = ["javac", str(src)]
        run_cmd = ["java", "-cp", str(temp_dir), class_name]

    elif language == "JavaScript":
        src = temp_dir / "script.js"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["node", str(src)]

    return run_cmd, compile_cmd


def _extract_java_class_name(code: str) -> Optional[str]:
    """Extract the public class name from Java source code."""
    import re
    match = re.search(r'\bpublic\s+class\s+(\w+)', code)
    if match:
        return match.group(1)
    match = re.search(r'\bclass\s+(\w+)', code)
    if match:
        return match.group(1)
    return None


def _run_subprocess(
    cmd: list[str],
    stdin_data: str = "",
    timeout: int = 10,
    cwd: Optional[Path] = None,
    process_ref: Optional[CodeRunner] = None,
) -> RunResult:
    """Run a command as a subprocess and capture output."""
    result = RunResult()
    start_time = time.monotonic()

    env = os.environ.copy()
    # Ensure PATH includes common binary locations
    env["PATH"] = "/usr/local/bin:/usr/bin:/bin:" + env.get("PATH", "")

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd) if cwd else None,
            env=env,
        )
        if process_ref is not None:
            process_ref._process = proc

        try:
            stdout_bytes, stderr_bytes = proc.communicate(
                input=stdin_data.encode("utf-8") if stdin_data else b"",
                timeout=timeout,
            )
            result.stdout = stdout_bytes.decode("utf-8", errors="replace")
            result.stderr = stderr_bytes.decode("utf-8", errors="replace")
            result.exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout_bytes, stderr_bytes = proc.communicate()
            result.stdout = stdout_bytes.decode("utf-8", errors="replace")
            result.stderr = stderr_bytes.decode("utf-8", errors="replace")
            result.timed_out = True
            result.exit_code = -1

    except FileNotFoundError as e:
        result.error_message = f"Command not found: {e}"
        result.exit_code = -1
    except PermissionError as e:
        result.error_message = f"Permission denied: {e}"
        result.exit_code = -1
    except Exception as e:
        result.error_message = f"Execution error: {e}"
        result.exit_code = -1

    result.elapsed_time = time.monotonic() - start_time
    return result
