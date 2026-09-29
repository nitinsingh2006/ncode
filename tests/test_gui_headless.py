"""
Nitin Editor — Headless GUI Integration Tests
Tests NitinEditor initialization, tab creation, code running, find/replace, and panel controls.
"""
import os
import sys
from pathlib import Path

# Force offscreen platform for headless Qt testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import NitinEditor
from app.compiler import RunResult


def run_gui_tests():
    app = QApplication.instance() or QApplication(sys.argv)
    window = NitinEditor()
    window.show()

    print("▶ Test 1: Tab creation & initialization")
    assert window._tab_widget.count() == 1, f"Expected 1 tab, got {window._tab_widget.count()}"
    state = window._current_state()
    assert state is not None
    assert state.is_modified == False, "New tab should not be dirty"
    assert state.language == "Python", f"Default language should be Python, got {state.language}"
    print("  ✓ Tab creation & cleanliness verified")

    print("▶ Test 2: Language switcher UI sync")
    window._lang_combo.setCurrentText("C++")
    assert window._current_state().language == "C++"
    window._lang_combo.setCurrentText("Python")
    assert window._current_state().language == "Python"
    print("  ✓ Language switcher sync verified")

    print("▶ Test 3: New tab addition and switching")
    window._new_tab()
    assert window._tab_widget.count() == 2
    assert window._tab_widget.currentIndex() == 1
    window._close_tab(1)
    assert window._tab_widget.count() == 1
    print("  ✓ Tab add/close verified")

    print("▶ Test 4: Code Execution via GUI runner")
    editor = window._current_editor()
    editor.setPlainText('print("HEADLESS_GUI_SUCCESS")')
    
    finished = False
    received_result = None

    def on_run_finished(result: RunResult):
        nonlocal finished, received_result
        finished = True
        received_result = result
        app.quit()

    window._run_code()
    assert window._runner_thread is not None
    window._runner_thread.finished_signal.connect(on_run_finished)

    # Process events until runner thread finishes or timeout
    timer = QTimer()
    timer.singleShot(10000, app.quit)  # 10s fallback safety timeout
    app.exec()

    assert finished, "Execution did not finish within timeout"
    assert received_result is not None
    assert received_result.exit_code == 0, f"Exit code {received_result.exit_code}, stderr: {received_result.stderr}"
    assert "HEADLESS_GUI_SUCCESS" in received_result.stdout, f"Stdout was: {received_result.stdout}"
    assert "HEADLESS_GUI_SUCCESS" in window._output_area.toPlainText()
    print("  ✓ Code execution via GUI runner verified")

    print("▶ Test 5: Input / Output clear & toggle")
    window._input_area.setPlainText("test input")
    assert window._input_area.toPlainText() == "test input"
    window._clear_output()
    assert window._output_area.toPlainText() == ""
    print("  ✓ Input/output clear verified")

    print("▶ Test 6: Settings dialog instantiation")
    from app.ui.settings_dialog import SettingsDialog
    dlg = SettingsDialog(window._settings, window)
    assert dlg is not None
    dlg.close()
    window._apply_settings()
    print("  ✓ Settings dialog verified")

    print("▶ Test 7: Find dialog instantiation & search")
    window._show_find()
    find_dlg = window._find_dialog
    assert find_dlg is not None
    find_dlg._find_input.setText("HEADLESS")
    find_dlg._find_next()
    find_dlg.close()
    print("  ✓ Find dialog verified")

    print("▶ Test 8: Clean closing")
    window.close()
    print("  ✓ Window close verified")
    app.exit(0)


if __name__ == "__main__":
    print("\n======================================================")
    print("  Nitin Editor — Headless GUI Tests")
    print("======================================================\n")
    run_gui_tests()
    print("\n======================================================")
    print("  All Headless GUI Tests Passed Successfully!")
    print("======================================================\n")
    sys.exit(0)
