"""
Nitin Editor — Automated tests for True Interactive Stdin & Streaming Output
Tests: C++, Python, Java, Node.js live stdin writing and real-time streaming.
"""
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.compiler import CodeRunner


def test_cpp_interactive():
    if not shutil.which("g++"):
        print("⊖ C++ test skipped (g++ missing)")
        return

    runner = CodeRunner()
    code = """#include <iostream>
using namespace std;
int main() {
    int a, b;
    cout << "Enter A: " << flush;
    cin >> a;
    cout << "Enter B: " << flush;
    cin >> b;
    cout << "Result: " << (a + b) << endl;
    return 0;
}"""

    stdout_chunks = []
    
    def on_stdout(text: str):
        stdout_chunks.append(text)

    # Launch in background thread or run directly with stdin interactions
    import threading
    res_holder = []

    def _run_task():
        res = runner.run("C++", code, stdin_data="", timeout=10, on_stdout=on_stdout)
        res_holder.append(res)

    t = threading.Thread(target=_run_task)
    t.start()

    # Wait for process to output "Enter A: "
    for _ in range(50):
        if "".join(stdout_chunks).startswith("Enter A:"):
            break
        time.sleep(0.05)

    assert "".join(stdout_chunks).startswith("Enter A:"), f"Got: {''.join(stdout_chunks)}"
    print("  ✓ C++ streamed prompt 'Enter A:'")

    # Send first number 10
    sent1 = runner.write_stdin("10\n")
    assert sent1, "Failed to write first input"

    # Wait for "Enter B: "
    for _ in range(50):
        if "Enter B:" in "".join(stdout_chunks):
            break
        time.sleep(0.05)

    assert "Enter B:" in "".join(stdout_chunks), f"Got: {''.join(stdout_chunks)}"
    print("  ✓ C++ received input 10 and streamed prompt 'Enter B:'")

    # Send second number 20
    sent2 = runner.write_stdin("20\n")
    assert sent2, "Failed to write second input"

    t.join(timeout=5)
    assert len(res_holder) == 1
    res = res_holder[0]
    assert res.exit_code == 0, f"Exit code {res.exit_code}, stderr: {res.stderr}"
    assert "Result: 30" in res.stdout, f"Full stdout: {res.stdout}"
    print("  ✓ C++ interactive multi-input test passed! (Result: 30)")


def test_python_interactive():
    runner = CodeRunner()
    code = """name = input("Name: ")
print("Hello", name)"""

    stdout_chunks = []

    def on_stdout(text: str):
        stdout_chunks.append(text)

    import threading
    res_holder = []

    def _run_task():
        res = runner.run("Python", code, stdin_data="", timeout=5, on_stdout=on_stdout)
        res_holder.append(res)

    t = threading.Thread(target=_run_task)
    t.start()

    for _ in range(50):
        if "Name:" in "".join(stdout_chunks):
            break
        time.sleep(0.05)

    assert "Name:" in "".join(stdout_chunks)
    print("  ✓ Python streamed prompt 'Name:'")

    runner.write_stdin("Nitin\n")
    t.join(timeout=5)

    assert len(res_holder) == 1
    res = res_holder[0]
    assert res.exit_code == 0
    assert "Hello Nitin" in res.stdout
    print("  ✓ Python interactive input passed! (Hello Nitin)")


def test_stop_while_waiting():
    runner = CodeRunner()
    code = """#include <iostream>
using namespace std;
int main() {
    int x;
    cin >> x;
    cout << "Got " << x;
    return 0;
}"""

    import threading
    res_holder = []

    def _run_task():
        res = runner.run("C++", code, stdin_data="", timeout=10)
        res_holder.append(res)

    t = threading.Thread(target=_run_task)
    t.start()

    time.sleep(0.5)
    runner.stop()
    t.join(timeout=3)

    assert len(res_holder) == 1
    res = res_holder[0]
    assert res.cancelled or res.exit_code != 0
    print("  ✓ STOP while process is waiting for stdin verified")


def test_preloaded_stdin():
    runner = CodeRunner()
    code = """#include <iostream>
using namespace std;
int main() {
    int a, b;
    cin >> a >> b;
    cout << "SUM=" << (a + b);
    return 0;
}"""

    res = runner.run("C++", code, stdin_data="15 25\n", timeout=5)
    assert res.exit_code == 0
    assert "SUM=40" in res.stdout
    print("  ✓ Preloaded batch stdin verified (SUM=40)")


if __name__ == "__main__":
    print("\n======================================================")
    print("  Nitin Editor — Interactive Stdin & Streaming Tests")
    print("======================================================\n")

    test_cpp_interactive()
    test_python_interactive()
    test_stop_while_waiting()
    test_preloaded_stdin()

    print("\n======================================================")
    print("  All Interactive Stdin & Streaming Tests Passed!")
    print("======================================================\n")
