"""
Nitin Editor — Python unit tests for compiler.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.compiler import (
    CodeRunner, detect_language, get_missing_tools, EXTENSION_MAP
)


def test_language_detection():
    cases = [
        ("main.cpp", "C++"),
        ("script.py", "Python"),
        ("Main.java", "Java"),
        ("index.html", "HTML"),
        ("app.js", "JavaScript"),
        ("styles.css", "CSS"),
        ("prog.c", "C"),
        ("code.cc", "C++"),
    ]
    for filename, expected in cases:
        result = detect_language(filename)
        assert result == expected, f"detect_language({filename!r}) = {result!r}, expected {expected!r}"
    print("✓ Language detection")


def test_python_run():
    runner = CodeRunner()
    result = runner.run("Python", 'print("Hello from Python")')
    assert result.exit_code == 0, f"Exit code: {result.exit_code}, stderr: {result.stderr}"
    assert "Hello from Python" in result.stdout
    print("✓ Python execution")


def test_python_stdin():
    runner = CodeRunner()
    code = "n = int(input())\nprint(n * 2)"
    result = runner.run("Python", code, stdin_data="21")
    assert result.exit_code == 0
    assert "42" in result.stdout
    print("✓ Python stdin")


def test_python_error():
    runner = CodeRunner()
    result = runner.run("Python", "1/0")
    assert result.exit_code != 0
    assert "ZeroDivisionError" in result.stderr or "ZeroDivisionError" in result.stdout
    print("✓ Python error handling")


def test_c_run():
    import shutil
    if not shutil.which("gcc"):
        print("⊖ C test skipped (gcc not found)")
        return
    runner = CodeRunner()
    code = '#include <stdio.h>\nint main(){printf("Hello from C\\n");return 0;}'
    result = runner.run("C", code)
    assert result.exit_code == 0, f"stderr: {result.stderr}"
    assert "Hello from C" in result.stdout
    print("✓ C execution")


def test_cpp_run():
    import shutil
    if not shutil.which("g++"):
        print("⊖ C++ test skipped (g++ not found)")
        return
    runner = CodeRunner()
    code = '#include <iostream>\nusing namespace std;\nint main(){cout<<"Hello from C++"<<endl;return 0;}'
    result = runner.run("C++", code)
    assert result.exit_code == 0, f"stderr: {result.stderr}"
    assert "Hello from C++" in result.stdout
    print("✓ C++ execution")


def test_cpp_stdin():
    import shutil
    if not shutil.which("g++"):
        print("⊖ C++ stdin test skipped")
        return
    runner = CodeRunner()
    code = '#include <iostream>\nusing namespace std;\nint main(){int a,b;cin>>a>>b;cout<<a+b;return 0;}'
    result = runner.run("C++", code, stdin_data="5 10")
    assert result.exit_code == 0
    assert "15" in result.stdout
    print("✓ C++ stdin (5+10=15)")


def test_javascript_run():
    import shutil
    if not shutil.which("node"):
        print("⊖ JavaScript test skipped (node not found)")
        return
    runner = CodeRunner()
    result = runner.run("JavaScript", 'console.log("Hello from JavaScript")')
    assert result.exit_code == 0
    assert "Hello from JavaScript" in result.stdout
    print("✓ JavaScript execution")


def test_timeout():
    runner = CodeRunner()
    result = runner.run("Python", "import time\ntime.sleep(100)", timeout=1)
    assert result.timed_out, "Expected timeout"
    print("✓ Execution timeout")


def test_java_run():
    import shutil
    if not shutil.which("javac") or not shutil.which("java"):
        print("⊖ Java test skipped (javac/java not found)")
        return
    runner = CodeRunner()
    code = 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello from Java");\n    }\n}'
    result = runner.run("Java", code)
    assert result.exit_code == 0, f"stderr: {result.stderr}"
    assert "Hello from Java" in result.stdout
    print("✓ Java execution")


if __name__ == "__main__":
    print("\n======================================================")
    print("  Nitin Editor — Compiler Tests")
    print("======================================================\n")

    tests = [
        test_language_detection,
        test_python_run,
        test_python_stdin,
        test_python_error,
        test_c_run,
        test_cpp_run,
        test_cpp_stdin,
        test_javascript_run,
        test_timeout,
        test_java_run,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ FAIL {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*54}")
    print(f"  {len(tests)-failed}/{len(tests)} tests passed")
    print(f"{'='*54}\n")

    sys.exit(0 if failed == 0 else 1)
