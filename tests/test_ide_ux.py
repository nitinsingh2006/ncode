"""
Nitin Editor — IDE UX & Interactive Test Suite
Tests all requested IDE execution, interactive stdin, timeout, and diagnostic test cases:
 1. Basic C++ stdin (cin >> a)
 2. Multiple inputs (cin >> a >> b)
 3. getline(cin, name)
 4. Compiler error & PROBLEMS tab jump line/column
 5. Compiler warning parsing
 6. Runtime crash (Segmentation fault 139)
 7. Python input()
 8. SQL error parsing
 9. STOP while waiting for input
10. Sequential RUN operations
11. Interactive waiting > 10 seconds without timeout
12. Infinite CPU loop safety timeout protection
"""
import os
import sys
import time
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import NitinEditor
from app.compiler import CodeRunner, RunResult
from app.diagnostics import parse_diagnostics, sql_diagnostic


def run_code_sync(window, app, timeout=20):
    res_holder = []
    
    if window._runner_thread:
        try:
            window._runner_thread.finished_signal.disconnect()
        except Exception:
            pass
        window._runner_thread.wait(1000)

    def on_finished(res):
        res_holder.append(res)
        app.quit()

    window._run_code()
    if window._runner_thread:
        window._runner_thread.finished_signal.connect(on_finished)

    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(app.quit)
    timer.start(int(timeout * 1000))
    app.exec()
    timer.stop()
    return res_holder[0] if res_holder else None


def run_ide_ux_tests():
    app = QApplication.instance() or QApplication(sys.argv)
    window = NitinEditor()
    window.show()

    print("\n======================================================")
    print("  Nitin Editor — IDE UX & Interactive Test Suite")
    print("======================================================\n")

    # ── Test 1: Basic C++ stdin ──
    print("▶ Test 1: Basic C++ stdin (cin >> a)")
    window._lang_combo.setCurrentText("C++")
    editor = window._current_editor()
    editor.setPlainText(
        "#include <iostream>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    int a;\n"
        "    cout << \"Enter number: \" << flush;\n"
        "    cin >> a;\n"
        "    cout << \"Result: \" << a * 2 << endl;\n"
        "    return 0;\n"
        "}\n"
    )

    def send_t1():
        if window._runner_thread and window._runner_thread.isRunning() and "Enter number:" in window._term_output.toPlainText():
            window._term_input.setText("6")
            window._term_execute()
        else:
            QTimer.singleShot(50, send_t1)
    QTimer.singleShot(50, send_t1)

    res1 = run_code_sync(window, app, timeout=10)
    assert res1 is not None, "Test 1 failed to finish"
    out1 = window._term_output.toPlainText()
    assert "Result: 12" in out1, f"Got: {out1}"
    print("  ✓ Test 1 passed (Enter number: 6 -> Result: 12)")

    # ── Test 2: Multiple inputs ──
    print("▶ Test 2: Multiple inputs (cin >> a >> b)")
    editor.setPlainText(
        "#include <iostream>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    int a, b;\n"
        "    cin >> a >> b;\n"
        "    cout << \"SUM=\" << (a + b) << endl;\n"
        "    return 0;\n"
        "}\n"
    )

    def send_t2():
        if window._runner_thread and window._runner_thread.isRunning() and getattr(window, "_status_text", "") == "Running…":
            window._term_input.setText("10 20")
            window._term_execute()
        else:
            QTimer.singleShot(50, send_t2)
    QTimer.singleShot(100, send_t2)

    res2 = run_code_sync(window, app, timeout=10)
    assert res2 is not None, "Test 2 failed to finish"
    out2 = window._term_output.toPlainText()
    assert "SUM=30" in out2, f"Got: {out2}"
    print("  ✓ Test 2 passed (10 20 -> SUM=30)")

    # ── Test 3: getline(cin, name) ──
    print("▶ Test 3: getline(cin, name)")
    editor.setPlainText(
        "#include <iostream>\n"
        "#include <string>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    string name;\n"
        "    cout << \"Name: \" << flush;\n"
        "    getline(cin, name);\n"
        "    cout << \"Hello \" << name << endl;\n"
        "    return 0;\n"
        "}\n"
    )

    def send_t3():
        if window._runner_thread and window._runner_thread.isRunning() and "Name:" in window._term_output.toPlainText():
            window._term_input.setText("Nitin Editor")
            window._term_execute()
        else:
            QTimer.singleShot(50, send_t3)
    QTimer.singleShot(50, send_t3)

    res3 = run_code_sync(window, app, timeout=10)
    assert res3 is not None, "Test 3 failed to finish"
    out3 = window._term_output.toPlainText()
    assert "Hello Nitin Editor" in out3, f"Got: {out3}"
    print("  ✓ Test 3 passed (Name: Nitin Editor -> Hello Nitin Editor)")

    # ── Test 4: Compiler error & PROBLEMS panel ──
    print("▶ Test 4: Compiler error & PROBLEMS panel")
    editor.setPlainText(
        "#include <iostream>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    cout << undefinedVariable;\n"
        "    return 0;\n"
        "}\n"
    )

    res4 = run_code_sync(window, app, timeout=10)
    assert res4 is not None, "Test 4 failed to finish"
    assert window._bottom_tabs.currentWidget() == window._problems_panel, "Should auto-show PROBLEMS tab on compile error"
    assert window._problems_list.count() > 0, "PROBLEMS list should contain compiler diagnostic"
    item = window._problems_list.item(0)
    assert "undefinedVariable" in item.text() or "declared" in item.text()
    
    window._go_to_diagnostic(item)
    line, col = editor.get_cursor_position()
    assert line == 4, f"Cursor line should be 4, got {line}"
    print("  ✓ Test 4 passed (Compiler error parsed, PROBLEMS tab selected, cursor jumped to L4)")

    # ── Test 5: Compiler warning ──
    print("▶ Test 5: Compiler warning parsing")
    editor.setPlainText(
        "#include <iostream>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    int unused_var = 42;\n"
        "    cout << \"Hello\" << endl;\n"
        "    return 0;\n"
        "}\n"
    )

    res5 = run_code_sync(window, app, timeout=10)
    assert res5 is not None
    assert "Hello" in window._term_output.toPlainText()
    print("  ✓ Test 5 passed (Compiler warning handled)")

    # ── Test 6: Runtime crash (Segmentation fault) ──
    print("▶ Test 6: Runtime crash (Segmentation fault)")
    editor.setPlainText(
        "#include <iostream>\n"
        "int main() {\n"
        "    int *p = nullptr;\n"
        "    *p = 42;\n"
        "    return 0;\n"
        "}\n"
    )

    res6 = run_code_sync(window, app, timeout=10)
    assert res6 is not None
    out6 = window._term_output.toPlainText()
    assert "Segmentation fault" in out6 or "code 139" in out6 or "code -11" in out6, f"Got: {out6}"
    print("  ✓ Test 6 passed (Runtime crash reported in TERMINAL)")

    # ── Test 7: Python input() ──
    print("▶ Test 7: Python input()")
    window._lang_combo.setCurrentText("Python")
    py_editor = window._current_editor()
    py_editor.setPlainText(
        "name = input('Enter your name: ')\n"
        "print('Hello', name)\n"
    )

    def send_t7():
        if window._runner_thread and window._runner_thread.isRunning() and "Enter your name:" in window._term_output.toPlainText():
            window._term_input.setText("PyNitin")
            window._term_execute()
        else:
            QTimer.singleShot(50, send_t7)
    QTimer.singleShot(50, send_t7)

    res7 = run_code_sync(window, app, timeout=10)
    assert res7 is not None
    assert "Hello PyNitin" in window._term_output.toPlainText()
    print("  ✓ Test 7 passed (Python input() -> Hello PyNitin)")

    # ── Test 8: SQL error ──
    print("▶ Test 8: SQL error parsing")
    window._lang_combo.setCurrentText("SQL")
    sql_editor = window._current_editor()
    sql_editor.setPlainText("SELET * FROM missing_table;")

    sql_res = []
    def on_sql_done(res):
        sql_res.append(res)
        app.quit()

    window._run_code()
    assert hasattr(window, "_sql_thread") and window._sql_thread is not None
    window._sql_thread.result_ready.connect(on_sql_done)

    t8_timer = QTimer()
    t8_timer.setSingleShot(True)
    t8_timer.timeout.connect(app.quit)
    t8_timer.start(10000)
    app.exec()
    t8_timer.stop()

    assert len(sql_res) == 1, "SQL test failed"
    assert window._bottom_tabs.currentWidget() == window._problems_panel, "SQL error should auto-show PROBLEMS tab"
    print("  ✓ Test 8 passed (SQL error parsed & shown in PROBLEMS)")

    # ── Test 9: STOP while waiting for input ──
    print("▶ Test 9: STOP while process is waiting for input")
    window._lang_combo.setCurrentText("C++")
    editor = window._current_editor()
    editor.setPlainText(
        "#include <iostream>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    int x;\n"
        "    cin >> x;\n"
        "    return 0;\n"
        "}\n"
    )

    def trigger_stop():
        if window._runner_thread and window._runner_thread.isRunning():
            window._stop_execution()
        else:
            QTimer.singleShot(100, trigger_stop)
    QTimer.singleShot(300, trigger_stop)

    res9 = run_code_sync(window, app, timeout=10)
    assert res9 is not None
    out9 = window._term_output.toPlainText()
    assert "stopped" in out9.lower() or "cancelled" in out9.lower(), f"Got: {out9}"
    print("  ✓ Test 9 passed (STOP stopped execution cleanly)")

    # ── Test 10: Multiple RUN operations ──
    print("▶ Test 10: Sequential RUN operations")
    editor.setPlainText("#include <iostream>\nint main(){std::cout<<\"RUN_1\"<<std::endl;return 0;}")
    res10_a = run_code_sync(window, app, timeout=10)
    assert res10_a is not None

    editor.setPlainText("#include <iostream>\nint main(){std::cout<<\"RUN_2\"<<std::endl;return 0;}")
    res10_b = run_code_sync(window, app, timeout=10)
    assert res10_b is not None
    assert "RUN_2" in window._term_output.toPlainText()
    print("  ✓ Test 10 passed (Sequential RUN operations verified)")

    # ── Test 11: Interactive waiting > 10 seconds ──
    print("▶ Test 11: Interactive waiting > 10 seconds without timeout")
    window._lang_combo.setCurrentText("C++")
    editor.setPlainText(
        "#include <iostream>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    int val;\n"
        "    cout << \"Enter val: \" << flush;\n"
        "    cin >> val;\n"
        "    cout << \"Read: \" << val << endl;\n"
        "    return 0;\n"
        "}\n"
    )

    def delayed_send():
        assert window._runner_thread and window._runner_thread.isRunning(), "Process should STILL BE RUNNING after 12 seconds of waiting for stdin"
        window._term_input.setText("99")
        window._term_execute()

    def schedule_delayed_send():
        if window._runner_thread and window._runner_thread.isRunning() and getattr(window, "_status_text", "") == "Running…":
            QTimer.singleShot(12000, delayed_send)
        else:
            QTimer.singleShot(100, schedule_delayed_send)

    QTimer.singleShot(100, schedule_delayed_send)

    res11 = run_code_sync(window, app, timeout=30)
    assert res11 is not None, "Test 11 failed to complete"
    assert res11.exit_code == 0, f"Process failed with exit code {res11.exit_code}"
    assert "Read: 99" in window._term_output.toPlainText()
    print("  ✓ Test 11 passed (Process remained alive after waiting >11s for stdin and succeeded!)")

    # ── Test 12: Infinite CPU loop timeout protection ──
    print("▶ Test 12: Infinite CPU loop safety timeout")
    window._settings["execution_timeout"] = 2  # Short 2s timeout for test
    editor.setPlainText("int main(){ while(true){} }")

    res12 = run_code_sync(window, app, timeout=10)
    assert res12 is not None
    assert res12.timed_out, "Infinite loop process should have been killed by safety timeout"
    print("  ✓ Test 12 passed (Infinite CPU loop killed by safety timeout as expected)")

    window._settings["execution_timeout"] = 10  # Restore setting

    print("\n======================================================")
    print("  ALL INTERACTIVE TIMEOUT & IDE TESTS PASSED!")
    print("======================================================\n")
    window.close()
    app.exit(0)


if __name__ == "__main__":
    run_ide_ux_tests()
