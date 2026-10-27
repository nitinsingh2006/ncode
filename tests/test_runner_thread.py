"""
Nitin Editor — Tests for RunnerThread (QThread integration)
"""
import sys
from pathlib import Path
from PySide6.QtCore import QCoreApplication

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.runner import RunnerThread
from app.compiler import RunResult


def test_runner_thread_python():
    app = QCoreApplication.instance() or QCoreApplication(sys.argv)

    runner = RunnerThread()
    runner.configure("Python", 'print("QThread Python Test")', stdin_data="", timeout=5)

    results = []

    def on_finished(res: RunResult):
        results.append(res)
        app.quit()

    runner.finished_signal.connect(on_finished)
    runner.start()
    app.exec()
    runner.wait(3000)

    assert len(results) == 1, "Expected 1 result"
    res = results[0]
    assert res.exit_code == 0
    assert "QThread Python Test" in res.stdout
    print("✓ RunnerThread Python test passed")


def test_runner_thread_stop():
    app = QCoreApplication.instance() or QCoreApplication(sys.argv)

    runner = RunnerThread()
    runner.configure("Python", 'import time\ntime.sleep(10)', stdin_data="", timeout=10)

    results = []

    def on_started():
        runner.stop_execution()

    def on_finished(res: RunResult):
        results.append(res)
        app.quit()

    runner.started_signal.connect(on_started)
    runner.finished_signal.connect(on_finished)
    runner.start()
    app.exec()
    runner.wait(3000)

    assert len(results) == 1, "Expected 1 result"
    res = results[0]
    assert res.cancelled or res.exit_code != 0
    print("✓ RunnerThread STOP test passed")


if __name__ == "__main__":
    print("\n======================================================")
    print("  Nitin Editor — RunnerThread Tests")
    print("======================================================\n")
    test_runner_thread_python()
    test_runner_thread_stop()
    print("\n✓ All RunnerThread tests passed!\n")
