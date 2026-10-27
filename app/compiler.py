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
    elif language in ("JavaScript", "TypeScript"):
        if not check_tool("node"):
            missing.append("node")
    elif language == "Rust":
        if not check_tool("rustc"):
            missing.append("rustc")
    elif language == "Go":
        if not check_tool("go"):
            missing.append("go")
    elif language == "Bash":
        if not check_tool("bash"):
            missing.append("bash")
    elif language == "Ruby":
        if not check_tool("ruby"):
            missing.append("ruby")
    elif language == "Perl":
        if not check_tool("perl"):
            missing.append("perl")
    elif language == "PHP":
        if not check_tool("php"):
            missing.append("php")
    elif language == "Kotlin":
        if not check_tool("kotlinc"):
            missing.append("kotlinc")
        if not check_tool("java"):
            missing.append("java")
    elif language == "Swift":
        if not check_tool("swift"):
            missing.append("swift")
    elif language == "C#":
        if not check_tool("dotnet") and not check_tool("mcs"):
            missing.append("dotnet")
    elif language == "Lua":
        if not check_tool("lua") and not check_tool("lua5.4"):
            missing.append("lua")
    elif language == "R":
        if not check_tool("Rscript"):
            missing.append("Rscript")
    elif language == "Dart":
        if not check_tool("dart"):
            missing.append("dart")
    elif language == "Scala":
        if not check_tool("scala"):
            missing.append("scala")
    elif language == "Haskell":
        if not check_tool("runhaskell") and not check_tool("ghc"):
            missing.append("ghc")
    elif language == "Julia":
        if not check_tool("julia"):
            missing.append("julia")
    elif language == "Zig":
        if not check_tool("zig"):
            missing.append("zig")
    elif language == "Elixir":
        if not check_tool("elixir"):
            missing.append("elixir")
    # SQL, HTML, CSS, JSON, YAML, Markdown don't require external compilers
    return missing


def _install_hint(language: str) -> str:
    hints: dict[str, str] = {
        "Python": "Install: sudo apt-get install python3",
        "C": "Install: sudo apt-get install gcc",
        "C++": "Install: sudo apt-get install g++",
        "Java": "Install: sudo apt-get install openjdk-21-jdk",
        "JavaScript": "Install: sudo apt-get install nodejs",
        "TypeScript": "Install: sudo apt-get install nodejs",
        "Rust": "Install: sudo apt-get install rustc (or curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh)",
        "Go": "Install: sudo apt-get install golang-go",
        "Bash": "Install: sudo apt-get install bash",
        "Ruby": "Install: sudo apt-get install ruby",
        "Perl": "Install: sudo apt-get install perl",
        "PHP": "Install: sudo apt-get install php-cli",
        "Kotlin": "Install: sudo apt-get install kotlin openjdk-21-jdk",
        "Swift": "Install Swift: https://www.swift.org/install/",
        "C#": "Install: sudo apt-get install dotnet-sdk-8.0",
        "Lua": "Install: sudo apt-get install lua5.4",
        "R": "Install: sudo apt-get install r-base",
        "Dart": "Install: sudo apt-get install dart",
        "Scala": "Install: sudo apt-get install scala",
        "Haskell": "Install: sudo apt-get install ghc",
        "Julia": "Install: sudo apt-get install julia",
        "Zig": "Install Zig: https://ziglang.org/download/",
        "Elixir": "Install: sudo apt-get install elixir",
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
            try:
                from app.preview import open_in_default_browser
                path = open_in_default_browser(code, is_css=(language == "CSS"), file_path=saved_path)
                result.exit_code = 0
                result.stdout = f"🌐 Opened {language} in default browser:\n    {path}\n"
                if on_stdout:
                    on_stdout(result.stdout)
                return result
            except Exception as e:
                result.error_message = f"Could not launch browser for {language}: {e}"
                result.exit_code = -1
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

    elif language == "TypeScript":
        src = temp_dir / "script.ts"
        src.write_text(code, encoding="utf-8")
        # Node.js v22.6+ supports TypeScript natively with --experimental-strip-types
        run_cmd = ["node", "--experimental-strip-types", str(src)]

    elif language == "Rust":
        src = temp_dir / "main.rs"
        src.write_text(code, encoding="utf-8")
        out = temp_dir / "main_rs"
        compile_cmd = ["rustc", str(src), "-o", str(out)]
        run_cmd = [str(out)]

    elif language == "Go":
        src = temp_dir / "main.go"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["go", "run", str(src)]

    elif language == "Bash":
        src = temp_dir / "script.sh"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["bash", str(src)]

    elif language == "Ruby":
        src = temp_dir / "script.rb"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["ruby", str(src)]

    elif language == "Perl":
        src = temp_dir / "script.pl"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["perl", str(src)]

    elif language == "PHP":
        src = temp_dir / "script.php"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["php", str(src)]

    elif language == "Kotlin":
        src = temp_dir / "main.kt"
        src.write_text(code, encoding="utf-8")
        out_jar = temp_dir / "main.jar"
        compile_cmd = ["kotlinc", str(src), "-include-runtime", "-d", str(out_jar)]
        run_cmd = ["java", "-jar", str(out_jar)]

    elif language == "Swift":
        src = temp_dir / "main.swift"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["swift", str(src)]

    elif language == "C#":
        src = temp_dir / "Program.cs"
        src.write_text(code, encoding="utf-8")
        if check_tool("dotnet"):
            run_cmd = ["dotnet", "run", "--project", str(temp_dir)]
        else:
            out_exe = temp_dir / "main.exe"
            compile_cmd = ["mcs", str(src), f"-out:{out_exe}"]
            run_cmd = ["mono", str(out_exe)]

    elif language == "Lua":
        src = temp_dir / "script.lua"
        src.write_text(code, encoding="utf-8")
        lua_bin = "lua" if check_tool("lua") else "lua5.4"
        run_cmd = [lua_bin, str(src)]

    elif language == "R":
        src = temp_dir / "script.r"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["Rscript", str(src)]

    elif language == "Dart":
        src = temp_dir / "script.dart"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["dart", "run", str(src)]

    elif language == "Scala":
        src = temp_dir / "main.scala"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["scala", str(src)]

    elif language == "Haskell":
        src = temp_dir / "main.hs"
        src.write_text(code, encoding="utf-8")
        if check_tool("runhaskell"):
            run_cmd = ["runhaskell", str(src)]
        else:
            out = temp_dir / "main_hs"
            compile_cmd = ["ghc", str(src), "-o", str(out)]
            run_cmd = [str(out)]

    elif language == "Julia":
        src = temp_dir / "script.jl"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["julia", str(src)]

    elif language == "Zig":
        src = temp_dir / "main.zig"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["zig", "run", str(src)]

    elif language == "Elixir":
        src = temp_dir / "script.exs"
        src.write_text(code, encoding="utf-8")
        run_cmd = ["elixir", str(src)]

    elif language in ("JSON", "YAML", "Markdown"):
        src = temp_dir / f"doc.{LANGUAGE_EXTENSIONS.get(language, '.txt')}"
        src.write_text(code, encoding="utf-8")
        # Validate syntax via python script and print formatted preview
        py_checker = (
            "import sys, json\n"
            "path = sys.argv[1]\n"
            "lang = sys.argv[2]\n"
            "with open(path, 'r', encoding='utf-8') as f:\n"
            "    content = f.read()\n"
            "if lang == 'JSON':\n"
            "    try:\n"
            "        data = json.loads(content)\n"
            "        print('✓ Valid JSON syntax')\n"
            "        print(json.dumps(data, indent=2)[:1000])\n"
            "    except Exception as e:\n"
            "        print('❌ Invalid JSON:', e, file=sys.stderr)\n"
            "        sys.exit(1)\n"
            "else:\n"
            "    print(f'✓ {lang} Document ({len(content.splitlines())} lines, {len(content)} bytes)')\n"
            "    print(content[:1000])\n"
        )
        run_cmd = ["python3", "-c", py_checker, str(src), language]

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
    # Include user-local bins (Go, Rust cargo, etc.) and standard paths
    home = str(Path.home())
    path_extras = [
        f"{home}/.local/bin",
        f"{home}/.cargo/bin",
        f"{home}/.local/go/bin",
        "/usr/local/go/bin",
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
    ]
    existing = env.get("PATH", "").split(":")
    new_paths = [p for p in path_extras if p not in existing]
    env["PATH"] = ":".join(new_paths) + ":" + env.get("PATH", "")
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
