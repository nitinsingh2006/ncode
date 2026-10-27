"""
Nitin Editor - main.py
Main application window and entry point.

Architecture:
  NitinEditor (QMainWindow)
    ├── QTabWidget  (editor tabs, each holding a CodeEditor)
    └── Integrated bottom panel (Problems, Output, Terminal)
  RunnerThread (QThread) — background execution, signals back to UI
  CodeRunner — subprocess management with stdin/timeout/stop support
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project root is importable when launched as a script
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PySide6.QtCore import Qt, QSize, QThread, Signal as Sig
from PySide6.QtGui import (
    QAction, QFont, QIcon, QKeySequence, QColor,
    QTextCursor, QTextDocument,
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QPlainTextEdit, QTextEdit, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QComboBox, QFileDialog, QMessageBox, QStatusBar,
    QToolBar, QMenu, QFrame, QDialog, QLineEdit, QCheckBox,
)

from app.compiler import (
    LANGUAGES, LANGUAGE_EXTENSIONS, TERMINAL_ENVS, detect_language,
    get_missing_tools, check_tool, _install_hint,
)
from app.runner import RunnerThread
from app.diagnostics import Diagnostic, parse_diagnostics, sql_diagnostic
from app.settings import load_settings, save_settings, load_recent_files, add_recent_file
from app.ui.settings_dialog import SettingsDialog

# SQL execution
from app.sql.executor import SQLExecutor, SQLResult

# Terminal
from app.terminal.command_runner import CommandRunner, CommandResult, get_host_os_name
from app.terminal.safety import check_command, warning_message
from app.terminal.history import load_history, save_history, add_command as history_add
from app.terminal.command_reference import get_reference_text, lookup_equivalents
from app.terminal.console import TerminalConsole

# AI Transpiler
from app.ai_transpiler import transpile_async, can_transpile

# Live Chatbot
try:
    from app.chatbot import ChatbotPanel
    _HAS_CHATBOT = True
except ImportError:
    _HAS_CHATBOT = False

# DSA Practice
try:
    from app.dsa.panel import DSAPanel
    from app.dsa.bank import Question, get_all_questions
    from app.dsa.storage import init_solutions_db, save_solution, get_solution
    from app.dsa.checker import check_solution_async, CheckResult
    from app.dsa.starters import make_full_editor_content, SUPPORTED_LANGS as DSA_LANGS
    from app.dsa.seed_questions import seed as seed_questions
    _HAS_DSA = True
except ImportError:
    _HAS_DSA = False

# Optional: preview
try:
    from app.preview import PreviewPanel, HAS_WEBENGINE
except ImportError:
    PreviewPanel = None  # type: ignore[assignment,misc]
    HAS_WEBENGINE = False

# Optional: custom editor with syntax highlighting
try:
    from app.editor import make_editor, CodeEditor
    _HAS_CUSTOM_EDITOR = True
except ImportError:
    _HAS_CUSTOM_EDITOR = False

ASSETS_DIR = _ROOT / "assets"
ICON_PATH = ASSETS_DIR / "icon.png"


def _extract_user_code(full_text: str, language: str) -> str:
    """
    Strip the DSA comment header block from editor content.
    Returns only the user's solution code (everything after the header).
    Supports '# ===...', '// ===...', '/* ... */', and triple quotes.
    """
    import re
    lines = full_text.splitlines()
    end_idx = -1

    # Check for triple-quote block
    if language == "Python":
        in_block = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('"""') and not in_block:
                in_block = True
                continue
            if in_block and '"""' in line:
                end_idx = i
                break

    # If not a triple quote, look for the closing boundary marker (===...)
    if end_idx == -1:
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(r"^(#|//|/\*|\*)\s*={10,}", stripped) or stripped.endswith("*/"):
                end_idx = i

    if end_idx != -1 and end_idx + 1 < len(lines):
        return "\n".join(lines[end_idx + 1:]).strip()

    return full_text.strip()



# ── Top-Level Worker Threads ──────────────────────────────────────────────────

class _SQLThread(QThread):
    result_ready = Sig(object)

    def __init__(self, sql_text: str, db_path_: Path | None, parent: QWidget | None = None):
        super().__init__(parent)
        self._sql = sql_text
        self._db = db_path_

    def run(self) -> None:
        executor = SQLExecutor()
        r = executor.execute(self._sql, db_path=self._db)
        self.result_ready.emit(r)


class _TermThread(QThread):
    stdout_sig = Sig(str)
    stderr_sig = Sig(str)
    done_sig = Sig(object)

    def __init__(self, command: str, os_: str, timeout_: int, cwd_: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._cmd = command
        self._os = os_
        self._timeout = timeout_
        self._cwd = cwd_
        self._runner = CommandRunner()

    def run(self) -> None:
        result = self._runner.run(
            command=self._cmd,
            target_os=self._os,
            timeout=self._timeout,
            cwd=self._cwd,
            on_stdout=lambda t: self.stdout_sig.emit(t),
            on_stderr=lambda t: self.stderr_sig.emit(t),
        )
        self.done_sig.emit(result)

    def stop(self) -> None:
        self._runner.stop()


# ── Default code snippets ────────────────────────────────────────────────────
DEFAULT_CODE: dict[str, str] = {
    "Python": '# Nitin Editor — Python\nprint("Hello, Nitin!")\n',
    "C": (
        '#include <stdio.h>\n\nint main() {\n'
        '    printf("Hello, Nitin!\\n");\n'
        '    return 0;\n}\n'
    ),
    "C++": (
        '#include <iostream>\nusing namespace std;\n\nint main() {\n'
        '    cout << "Hello, Nitin!" << endl;\n'
        '    return 0;\n}\n'
    ),
    "Java": (
        'public class Main {\n'
        '    public static void main(String[] args) {\n'
        '        System.out.println("Hello, Nitin!");\n'
        '    }\n}\n'
    ),
    "JavaScript": '// Nitin Editor — JavaScript\nconsole.log("Hello, Nitin!");\n',
    "HTML": (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '  <title>Nitin Editor — HTML Preview</title>\n'
        '  <style>\n'
        '    /* ── Inline CSS ── */\n'
        '    body {\n'
        '      margin: 0;\n'
        '      font-family: "Segoe UI", Roboto, Arial, sans-serif;\n'
        '      background: linear-gradient(135deg, #1e1e2e, #313244);\n'
        '      color: #cdd6f4;\n'
        '      display: flex;\n'
        '      flex-direction: column;\n'
        '      align-items: center;\n'
        '      justify-content: center;\n'
        '      min-height: 100vh;\n'
        '    }\n'
        '    h1 { color: #89b4fa; font-size: 2.5rem; margin-bottom: 0.25rem; }\n'
        '    p  { color: #a6adc8; font-size: 1.1rem; }\n'
        '    button {\n'
        '      margin-top: 1rem;\n'
        '      padding: 0.6rem 1.6rem;\n'
        '      background: #89b4fa;\n'
        '      color: #1e1e2e;\n'
        '      border: none;\n'
        '      border-radius: 8px;\n'
        '      font-size: 1rem;\n'
        '      cursor: pointer;\n'
        '      transition: background 0.2s;\n'
        '    }\n'
        '    button:hover { background: #b4befe; }\n'
        '    #output { margin-top: 1rem; font-size: 1rem; color: #a6e3a1; }\n'
        '  </style>\n'
        '</head>\n'
        '<body>\n'
        '  <h1>Hello, Nitin! 🚀</h1>\n'
        '  <p>Welcome to <strong>Nitin Editor</strong> — HTML + CSS + JS together!</p>\n'
        '  <button onclick="greet()">Click me</button>\n'
        '  <p id="output"></p>\n\n'
        '  <script>\n'
        '    /* ── Inline JavaScript ── */\n'
        '    function greet() {\n'
        '      document.getElementById("output").textContent =\n'
        '        "🎉 JavaScript is working perfectly!";\n'
        '    }\n'
        '  </script>\n'
        '</body>\n'
        '</html>\n'
    ),
    "CSS": (
        '/* CSS Preview */\nbody {\n    background: #1e1e2e;\n'
        '    color: #cdd6f4;\n    font-family: Arial, sans-serif;\n'
        '    padding: 20px;\n}\n\nh1 {\n    color: #89b4fa;\n}\n'
    ),
    "SQL": (
        '-- SQL (SQLite) — Nitin Editor\n'
        'CREATE TABLE IF NOT EXISTS students (\n'
        '    id      INTEGER PRIMARY KEY,\n'
        '    name    TEXT    NOT NULL,\n'
        '    marks   INTEGER\n'
        ');\n\n'
        "INSERT INTO students VALUES (1, 'Amit', 85), (2, 'Rahul', 92);\n\n"
        'SELECT * FROM students;\n'
    ),
}

# ── Colours ──────────────────────────────────────────────────────────────────
OUTPUT_BG = "#11111b"
OUTPUT_FG = "#cdd6f4"
INPUT_BG  = "#181825"

# ── Stylesheets ──────────────────────────────────────────────────────────────
DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", "Ubuntu", "Inter", Arial, sans-serif;
    font-size: 13px;
}
QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
    padding: 2px 4px;
}
QMenuBar::item { padding: 4px 10px; border-radius: 3px; }
QMenuBar::item:selected { background-color: #313244; }
QMenu {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item { padding: 5px 24px; border-radius: 3px; }
QMenu::item:selected { background-color: #313244; }
QMenu::separator { height: 1px; background: #313244; margin: 3px 8px; }
QToolBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    padding: 4px 6px;
    spacing: 4px;
}
QToolBar::separator { width: 1px; background: #313244; margin: 2px 4px; }
QTabWidget::pane { border: none; background-color: #1e1e2e; }
QTabBar { background-color: #181825; }
QTabBar::tab {
    background-color: #181825;
    color: #7f849c;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 7px 18px;
    font-size: 12px;
    min-width: 80px;
}
QTabBar::tab:selected {
    color: #cdd6f4;
    border-bottom: 2px solid #89b4fa;
    background-color: #1e1e2e;
    font-weight: 600;
}
QTabBar::tab:hover:!selected {
    color: #a6adc8;
    background-color: #24273a;
}
QSplitter::handle {
    background-color: #313244;
}
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:vertical   { height: 2px; }
QPlainTextEdit, QTextEdit {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: none;
    selection-background-color: #313244;
    font-family: "JetBrains Mono", "Fira Code", "Consolas", "Courier New", monospace;
}
QScrollBar:vertical {
    background: #181825; width: 8px; border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #45475a; border-radius: 4px; min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #6c7086; }
QScrollBar:horizontal {
    background: #181825; height: 8px; border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #45475a; border-radius: 4px; min-width: 24px;
}
QScrollBar::add-line, QScrollBar::sub-line { background: none; border: none; }
QStatusBar {
    background-color: #181825;
    color: #7f849c;
    border-top: 1px solid #313244;
    font-size: 11px;
    padding: 0 4px;
}
QStatusBar::item { border: none; }
QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 4px 10px;
    min-width: 110px;
    font-size: 12px;
}
QComboBox:hover { border-color: #89b4fa; }
QComboBox::drop-down { border: none; padding-right: 6px; }
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 2px;
}
QLineEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 5px 8px;
}
QLineEdit:focus { border-color: #89b4fa; }
QCheckBox { color: #cdd6f4; spacing: 6px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    background: #313244;
    border: 1px solid #45475a;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    background: #89b4fa;
    border-color: #89b4fa;
}
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 5px 14px;
    font-size: 12px;
}
QPushButton:hover { background-color: #45475a; }
QPushButton:pressed { background-color: #585b70; }
QPushButton:disabled { color: #585b70; border-color: #313244; }
QDialog { background-color: #1e1e2e; }
QMessageBox { background-color: #1e1e2e; }
"""

BTN_RUN_STYLE = """
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #40a02b,stop:1 #2d7e1f);
    color: white;
    border: none;
    border-radius: 5px;
    padding: 6px 20px;
    font-size: 13px;
    font-weight: bold;
    min-width: 90px;
}
QPushButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #4ec135,stop:1 #36a024);
}
QPushButton:pressed { background: #2d7e1f; }
QPushButton:disabled { background: #313244; color: #585b70; border: none; }
"""

BTN_STOP_STYLE = """
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #d20f39,stop:1 #a0102a);
    color: white;
    border: none;
    border-radius: 5px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: bold;
    min-width: 80px;
}
QPushButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #e81a44,stop:1 #b8153a);
}
QPushButton:pressed { background: #a0102a; }
QPushButton:disabled { background: #313244; color: #585b70; border: none; }
"""

BTN_PREVIEW_STYLE = """
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1e66f5,stop:1 #1353c5);
    color: white;
    border: none;
    border-radius: 5px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: bold;
    min-width: 90px;
}
QPushButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #2a78ff,stop:1 #1a64e0);
}
QPushButton:pressed { background: #1353c5; }
QPushButton:disabled { background: #313244; color: #585b70; border: none; }
"""


# ── Tab document state ────────────────────────────────────────────────────────

class TabState:
    """Holds per-tab metadata."""
    _counter = 0

    def __init__(
        self,
        title: str = "Untitled",
        language: str = "Python",
        file_path: Path | None = None,
    ) -> None:
        TabState._counter += 1
        self.tab_id = TabState._counter
        self.title = title
        self.language = language
        self.file_path: Path | None = file_path
        self.is_modified = False
        self.dsa_question = None

    @property
    def display_title(self) -> str:
        marker = "● " if self.is_modified else ""
        return f"{marker}{self.title}"


# ── Find/Replace Dialog ──────────────────────────────────────────────────────

class FindReplaceDialog(QDialog):
    """Non-modal find & replace dialog."""

    def __init__(self, editor_getter, parent=None) -> None:
        super().__init__(parent)
        self._get_editor = editor_getter
        self.setWindowTitle("Find & Replace")
        self.setModal(False)
        self.setMinimumWidth(400)
        self.setStyleSheet(DARK_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 12)

        # Find row
        find_row = QHBoxLayout()
        lbl = QLabel("Find:")
        lbl.setFixedWidth(60)
        find_row.addWidget(lbl)
        self._find_input = QLineEdit()
        self._find_input.setPlaceholderText("Search text…")
        self._find_input.returnPressed.connect(self._find_next)
        find_row.addWidget(self._find_input)
        layout.addLayout(find_row)

        # Replace row
        replace_row = QHBoxLayout()
        lbl2 = QLabel("Replace:")
        lbl2.setFixedWidth(60)
        replace_row.addWidget(lbl2)
        self._replace_input = QLineEdit()
        self._replace_input.setPlaceholderText("Replacement text…")
        replace_row.addWidget(self._replace_input)
        layout.addLayout(replace_row)

        # Options
        opts_row = QHBoxLayout()
        self._case_sensitive = QCheckBox("Case sensitive")
        self._whole_word = QCheckBox("Whole word")
        opts_row.addWidget(self._case_sensitive)
        opts_row.addWidget(self._whole_word)
        opts_row.addStretch()
        layout.addLayout(opts_row)

        # Status
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #7f849c; font-size: 11px;")
        layout.addWidget(self._status_label)

        # Buttons
        btn_row = QHBoxLayout()
        for label, slot in (
            ("Find Next", self._find_next),
            ("Replace", self._replace),
            ("Replace All", self._replace_all),
            ("Close", self.close),
        ):
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

    def open_with_focus(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()
        self._find_input.setFocus()
        self._find_input.selectAll()

    def _get_flags(self) -> QTextDocument.FindFlag:
        flags = QTextDocument.FindFlag(0)
        if self._case_sensitive.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if self._whole_word.isChecked():
            flags |= QTextDocument.FindFlag.FindWholeWords
        return flags

    def _find_next(self) -> bool:
        query = self._find_input.text()
        if not query:
            return False
        editor = self._get_editor()
        if editor is None:
            return False
        flags = self._get_flags()
        found = editor.find(query, flags)
        if not found:
            # Wrap around
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            editor.setTextCursor(cursor)
            found = editor.find(query, flags)
        if found:
            self._status_label.setText("")
        else:
            self._status_label.setText(f'Not found: "{query}"')
        return found

    def _replace(self) -> None:
        editor = self._get_editor()
        if editor is None:
            return
        query = self._find_input.text()
        replace = self._replace_input.text()
        if not query:
            return
        cursor = editor.textCursor()
        if cursor.hasSelection():
            sel = cursor.selectedText()
            matches = sel == query if self._case_sensitive.isChecked() else sel.lower() == query.lower()
            if matches:
                cursor.insertText(replace)
        self._find_next()

    def _replace_all(self) -> None:
        editor = self._get_editor()
        if editor is None:
            return
        query = self._find_input.text()
        replace = self._replace_input.text()
        if not query:
            return
        text = editor.get_text()
        if self._case_sensitive.isChecked():
            count = text.count(query)
            new_text = text.replace(query, replace)
        else:
            import re
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            count = len(pattern.findall(text))
            new_text = pattern.sub(replace, text)
        if count:
            editor.set_text(new_text)
            self._status_label.setText(f"Replaced {count} occurrence(s).")
        else:
            self._status_label.setText(f'Not found: "{query}"')



class _TermInputCompat:
    """Backward compatibility wrapper for self._term_input used by tests/helpers."""

    def __init__(self, console: TerminalConsole):
        self._console = console

    def text(self) -> str:
        return self._console.get_current_input()

    def clear(self) -> None:
        self._console.set_input_text("")

    def setText(self, val: str) -> None:
        self._console.set_input_text(val)

    def setPlaceholderText(self, text: str) -> None:
        pass

    def setFocus(self) -> None:
        self._console.setFocus()

    def selectAll(self) -> None:
        pass

    def installEventFilter(self, obj) -> None:
        pass


# ── Main Window ───────────────────────────────────────────────────────────────

class NitinEditor(QMainWindow):


    def __init__(self, initial_file: Path | None = None) -> None:
        super().__init__()
        self._settings = load_settings()
        self._runner_thread: RunnerThread | None = None
        self._tab_states: dict[int, TabState] = {}   # id(container) → TabState
        self._find_dialog: FindReplaceDialog | None = None
        self._preview_dialog: QDialog | None = None
        self._preview_panel = None  # Created lazily

        # Terminal state
        self._term_runner: CommandRunner | None = None
        self._term_runner_thread = None  # QThread wrapping CommandRunner
        self._term_history: list[str] = load_history()
        self._term_history_pos: int = -1    # position in history browsing
        self._term_running: bool = False
        self._sql_db_path: Path | None = None  # None = temporary

        # AI Transpiler state
        self._prev_language: str = "Python"   # language before the switch
        self._transpile_in_progress: bool = False  # guard against re-entrancy

        # DSA Practice state
        self._dsa_panel: "DSAPanel | None" = None
        self._active_dsa_question: "Question | None" = None   # currently open question
        self._dsa_checking: bool = False   # guard: one check at a time

        # Live Chatbot state
        self._chatbot_panel: "ChatbotPanel | None" = None

        self._setup_window()
        self._build_ui()
        self._apply_settings()
        self._new_tab()   # Start with one empty tab

        # Global event filter for universal shortcuts (Zoom In/Out/Reset)
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

        if initial_file and initial_file.exists():
            self._open_file_path(initial_file)


    # ── Window setup ─────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle("Nitin Editor")
        self.setMinimumSize(1000, 650)
        self.resize(1280, 800)
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

    # ── UI building ───────────────────────────────────────────────────────────

    # ── UI building ───────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._create_actions()
        self._build_menu_bar()
        self._build_toolbar()
        self._build_central()
        self._build_status_bar()

    def _create_actions(self) -> None:
        self._action_new = QAction("📄 &New Tab", self)
        self._action_new.setShortcuts([QKeySequence("Ctrl+N"), QKeySequence("Ctrl+T")])
        self._action_new.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        self._action_new.setToolTip("Create a new untitled tab (Ctrl+N)")
        self._action_new.triggered.connect(lambda: self._new_tab())

        self._action_open = QAction("📂 &Open…", self)
        self._action_open.setShortcut(QKeySequence("Ctrl+O"))
        self._action_open.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        self._action_open.setToolTip("Open file (Ctrl+O)")
        self._action_open.triggered.connect(self._open_file)

        self._action_save = QAction("💾 &Save", self)
        self._action_save.setShortcut(QKeySequence("Ctrl+S"))
        self._action_save.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        self._action_save.setToolTip("Save current file (Ctrl+S)")
        self._action_save.triggered.connect(self._save_file)

        self._action_save_as = QAction("Save &As…", self)
        self._action_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._action_save_as.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        self._action_save_as.triggered.connect(self._save_file_as)

        self._action_close_tab = QAction("Close Tab", self)
        self._action_close_tab.setShortcut(QKeySequence("Ctrl+W"))
        self._action_close_tab.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        self._action_close_tab.triggered.connect(self._close_current_tab)

        self._action_run = QAction("▶  &Run", self)
        self._action_run.setShortcuts([QKeySequence("Ctrl+Return"), QKeySequence("F5")])
        self._action_run.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        self._action_run.setToolTip("Run code (Ctrl+Enter or F5)")
        self._action_run.triggered.connect(self._run_code)

        self._action_stop = QAction("■  &Stop", self)
        self._action_stop.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self._action_stop.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        self._action_stop.setToolTip("Stop execution (Ctrl+Shift+C)")
        self._action_stop.triggered.connect(self._stop_execution)

        self._action_find = QAction("&Find…", self)
        self._action_find.setShortcut(QKeySequence("Ctrl+F"))
        self._action_find.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        self._action_find.triggered.connect(self._show_find)

        self._action_replace = QAction("Find && &Replace…", self)
        self._action_replace.setShortcut(QKeySequence("Ctrl+H"))
        self._action_replace.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        self._action_replace.triggered.connect(self._show_find_replace)

        self._action_open_terminal = QAction("⌨  &Terminal", self)
        # Ctrl+Shift+T: does not conflict with existing shortcuts
        self._action_open_terminal.setShortcut(QKeySequence("Ctrl+Shift+T"))
        self._action_open_terminal.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        self._action_open_terminal.setToolTip("Open Terminal panel (Ctrl+Shift+T)")
        self._action_open_terminal.triggered.connect(self._show_terminal_panel)

    def _build_menu_bar(self) -> None:
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("&File")
        file_menu.addAction(self._action_new)
        file_menu.addAction(self._action_open)
        file_menu.addSeparator()
        file_menu.addAction(self._action_save)
        file_menu.addAction(self._action_save_as)
        file_menu.addSeparator()
        self._recent_menu = file_menu.addMenu("Recent Files")
        self._refresh_recent_menu()
        file_menu.addSeparator()
        self._add_menu_action(file_menu, "E&xit",            self.close,             "Ctrl+Q")

        # Edit
        edit_menu = mb.addMenu("&Edit")
        self._add_menu_action(edit_menu, "&Undo",            self._undo,             "Ctrl+Z")
        self._add_menu_action(edit_menu, "&Redo",            self._redo,             "Ctrl+Y")
        edit_menu.addSeparator()
        self._add_menu_action(edit_menu, "Cu&t",             self._cut,              "Ctrl+X")
        self._add_menu_action(edit_menu, "&Copy",            self._copy,             "Ctrl+C")
        self._add_menu_action(edit_menu, "&Paste",           self._paste,            "Ctrl+V")
        self._add_menu_action(edit_menu, "Select &All",      self._select_all,       "Ctrl+A")
        edit_menu.addSeparator()
        edit_menu.addAction(self._action_find)
        edit_menu.addAction(self._action_replace)

        # View
        view_menu = mb.addMenu("&View")
        self._action_zoom_in = self._add_menu_action(
            view_menu, "Zoom &In", self._zoom_in,
            [QKeySequence.StandardKey.ZoomIn, "Ctrl+=", "Ctrl++", "Ctrl+Shift+="]
        )
        self._action_zoom_out = self._add_menu_action(
            view_menu, "Zoom &Out", self._zoom_out,
            [QKeySequence.StandardKey.ZoomOut, "Ctrl+-", "Ctrl+_", "Ctrl+Shift+-"]
        )
        self._action_zoom_reset = self._add_menu_action(
            view_menu, "Reset &Zoom", self._zoom_reset, "Ctrl+0"
        )

        # Run
        run_menu = mb.addMenu("&Run")
        run_menu.addAction(self._action_run)
        run_menu.addAction(self._action_stop)
        run_menu.addSeparator()
        self._add_menu_action(run_menu, "🌐  &Preview (HTML/CSS)", self._show_preview, "Ctrl+Shift+P")

        # Terminal
        terminal_menu = mb.addMenu("&Terminal")
        terminal_menu.addAction(self._action_open_terminal)
        terminal_menu.addSeparator()
        self._add_menu_action(terminal_menu, "Command &Reference", self._show_command_reference)
        self._add_menu_action(terminal_menu, "Environment &Info", self._show_env_info)

        # Tabs
        tab_menu = mb.addMenu("&Tabs")
        tab_menu.addAction(self._action_new)
        tab_menu.addAction(self._action_close_tab)
        self._add_menu_action(tab_menu, "Next Tab",          self._next_tab,         "Ctrl+Tab")
        self._add_menu_action(tab_menu, "Previous Tab",      self._prev_tab,         "Ctrl+Shift+Tab")

        # Settings
        settings_menu = mb.addMenu("&Settings")
        self._add_menu_action(settings_menu, "⚙  Preferences…", self._show_settings)

        # DSA Practice
        if _HAS_DSA:
            dsa_menu = mb.addMenu("🧩 &DSA")
            self._add_menu_action(dsa_menu, "Toggle &Sidebar", self._dsa_toggle_sidebar, "Ctrl+Shift+D")
            dsa_menu.addSeparator()
            self._add_menu_action(dsa_menu, "🎯  &Check Solution", self._dsa_check_solution, "Ctrl+Shift+G")
            dsa_menu.addSeparator()
            self._add_menu_action(dsa_menu, "↻  &Refresh Questions", self._dsa_refresh)

        # Live Chatbot
        if _HAS_CHATBOT:
            chat_menu = mb.addMenu("💬 &Chat")
            self._add_menu_action(chat_menu, "Toggle &Chatbot", self._chatbot_toggle, "Ctrl+Shift+I")

        # Help
        help_menu = mb.addMenu("&Help")
        self._add_menu_action(help_menu, "&About",           self._show_about)
        self._add_menu_action(help_menu, "Keyboard &Shortcuts", self._show_shortcuts)
        self._add_menu_action(help_menu, "Compiler &Status", self._show_compiler_status)

    def _add_menu_action(
        self,
        menu: QMenu,
        text: str,
        slot,
        shortcut: str | list[str | QKeySequence] | QKeySequence | None = None,
    ) -> QAction:
        action = QAction(text, self)
        if shortcut:
            if isinstance(shortcut, list):
                seqs = [QKeySequence(s) if isinstance(s, str) else s for s in shortcut]
                action.setShortcuts(seqs)
            elif isinstance(shortcut, str):
                action.setShortcut(QKeySequence(shortcut))
            else:
                action.setShortcut(shortcut)
            action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main", self)
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        tb.setStyleSheet("QToolBar { padding: 4px 8px; spacing: 6px; }")
        self.addToolBar(tb)

        def tb_action(text: str, slot, shortcut: str | None = None, tip: str = "") -> QAction:
            a = QAction(text, self)
            if shortcut:
                a.setShortcut(QKeySequence(shortcut))
            a.setToolTip(tip or text)
            a.triggered.connect(slot)
            return a

        tb.addAction(self._action_new)
        tb.addAction(self._action_open)
        tb.addAction(self._action_save)
        tb.addSeparator()

        lang_label = QLabel("  Language: ")
        lang_label.setStyleSheet("color: #7f849c; font-size: 12px;")
        tb.addWidget(lang_label)

        self._lang_combo = QComboBox()
        for lang in LANGUAGES:
            self._lang_combo.addItem(lang)
        self._lang_combo.setCurrentText("Python")
        self._lang_combo.currentTextChanged.connect(self._on_language_changed)
        self._lang_combo.setToolTip("Select programming language")
        tb.addWidget(self._lang_combo)

        tb.addSeparator()

        self._run_btn = QPushButton("▶  RUN")
        self._run_btn.setStyleSheet(BTN_RUN_STYLE)
        self._run_btn.setToolTip("Run code (Ctrl+Enter or F5)")
        self._run_btn.clicked.connect(self._run_code)
        tb.addWidget(self._run_btn)

        self._stop_btn = QPushButton("■  STOP")
        self._stop_btn.setStyleSheet(BTN_STOP_STYLE)
        self._stop_btn.setToolTip("Stop execution (Ctrl+Shift+C)")
        self._stop_btn.clicked.connect(self._stop_execution)
        self._stop_btn.setEnabled(False)
        tb.addWidget(self._stop_btn)

        self._preview_btn = QPushButton("🌐 Preview")
        self._preview_btn.setStyleSheet(BTN_PREVIEW_STYLE)
        self._preview_btn.setToolTip("Preview HTML/CSS (Ctrl+Shift+P)")
        self._preview_btn.clicked.connect(self._show_preview)
        self._preview_btn.setVisible(False)
        tb.addWidget(self._preview_btn)

        self._browser_btn = QPushButton("🌍 Browser")
        self._browser_btn.setStyleSheet(BTN_PREVIEW_STYLE)
        self._browser_btn.setToolTip("Open in default system browser (Ctrl+Shift+B)")
        self._browser_btn.clicked.connect(self._open_in_browser)
        self._browser_btn.setVisible(False)
        tb.addWidget(self._browser_btn)

        tb.addSeparator()

        # DSA submit button (only visible when a question is open)
        self._dsa_submit_btn = QPushButton("🎯  Check Solution")
        self._dsa_submit_btn.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #8839ef,stop:1 #6c2da0); color:white; border:none; "
            "border-radius:5px; padding:6px 14px; font-size:12px; font-weight:bold; }"
            "QPushButton:hover { background:#9b4ff5; }"
            "QPushButton:disabled { background:#313244; color:#585b70; border:none; }"
        )
        self._dsa_submit_btn.setToolTip("Check your DSA solution with AI (Ctrl+Shift+G)")
        self._dsa_submit_btn.clicked.connect(self._dsa_check_solution)
        self._dsa_submit_btn.setVisible(False)
        tb.addWidget(self._dsa_submit_btn)

        tb.addSeparator()

        # Chatbot toggle button
        if _HAS_CHATBOT:
            self._chatbot_btn = QPushButton("💬 Chat")
            self._chatbot_btn.setCheckable(True)
            self._chatbot_btn.setStyleSheet(
                "QPushButton { background:#313244; color:#cba6f7; border:none; "
                "border-radius:5px; padding:6px 14px; font-size:12px; font-weight:bold; }"
                "QPushButton:hover { background:#45475a; }"
                "QPushButton:checked { background:#cba6f7; color:#1e1e2e; }"
            )
            self._chatbot_btn.setToolTip("Toggle AI Chatbot panel (Ctrl+Shift+I)")
            self._chatbot_btn.clicked.connect(self._chatbot_toggle)
            tb.addWidget(self._chatbot_btn)
        else:
            self._chatbot_btn = None

        tb.addSeparator()
        tb.addAction(tb_action("⚙", self._show_settings, tip="Preferences"))

    def _build_central(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Horizontal splitter: DSA sidebar | editor area
        self._h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # DSA sidebar (hidden by default)
        if _HAS_DSA:
            try:
                seed_questions()          # no-op if already seeded
                init_solutions_db()
                self._dsa_panel = DSAPanel()
                self._dsa_panel.question_selected.connect(self._dsa_open_question)
                self._h_splitter.addWidget(self._dsa_panel)
                self._dsa_panel.setVisible(False)   # hidden until toggled
            except Exception as _e:
                self._dsa_panel = None

        # Editor + bottom panel (vertical)
        editor_area = QWidget()
        editor_vbox = QVBoxLayout(editor_area)
        editor_vbox.setContentsMargins(0, 0, 0, 0)
        editor_vbox.setSpacing(0)

        self._tab_widget = QTabWidget()
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.setMovable(True)
        self._tab_widget.tabCloseRequested.connect(self._close_tab)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

        self._v_splitter = QSplitter(Qt.Orientation.Vertical)
        self._v_splitter.addWidget(self._tab_widget)

        self._bottom_tabs = QTabWidget()
        self._bottom_tabs.setDocumentMode(True)
        self._problems_panel = self._make_problems_panel()
        self._output_panel = self._make_output_panel()
        self._terminal_panel_widget = self._make_integrated_terminal_panel()
        self._dsa_feedback_panel = self._make_dsa_feedback_panel()
        self._bottom_tabs.addTab(self._problems_panel, "PROBLEMS  0")
        self._bottom_tabs.addTab(self._output_panel, "OUTPUT")
        self._bottom_tabs.addTab(self._terminal_panel_widget, "TERMINAL")
        self._bottom_tabs.addTab(self._dsa_feedback_panel, "🎯 DSA FEEDBACK")
        self._v_splitter.addWidget(self._bottom_tabs)
        self._v_splitter.setSizes([520, 200])

        editor_vbox.addWidget(self._v_splitter)
        self._h_splitter.addWidget(editor_area)

        # Chatbot panel (right side, hidden by default)
        if _HAS_CHATBOT:
            try:
                self._chatbot_panel = ChatbotPanel()
                self._chatbot_panel.insert_to_editor.connect(self._chatbot_insert_to_editor)
                self._chatbot_panel.insert_and_run.connect(self._chatbot_insert_and_run)
                self._chatbot_panel.run_in_terminal.connect(self._chatbot_run_terminal_command)
                self._h_splitter.addWidget(self._chatbot_panel)
                self._chatbot_panel.setVisible(False)   # hidden until toggled
                self._chatbot_panel.setMinimumWidth(280)
            except Exception:
                self._chatbot_panel = None

        self._h_splitter.setSizes([280, 1000, 0])

        root.addWidget(self._h_splitter)

    def _make_problems_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 4, 6, 4)
        self._problems_list = QListWidget()
        self._problems_list.setStyleSheet(
            "QListWidget{background:#11111b;color:#cdd6f4;border:none;font-family:monospace;}"
            "QListWidget::item{padding:6px;border-bottom:1px solid #313244;}"
            "QListWidget::item:selected{background:#313244;}"
        )
        self._problems_list.itemActivated.connect(self._go_to_diagnostic)
        self._problems_list.itemClicked.connect(self._go_to_diagnostic)
        layout.addWidget(self._problems_list)
        return panel

    def _make_output_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with Clear button
        hdr = QWidget()
        hdr.setFixedHeight(32)
        hdr.setStyleSheet("background:#1a1a2e; border-bottom: 1px solid #313244;")
        hbox = QHBoxLayout(hdr)
        hbox.setContentsMargins(10, 0, 6, 0)
        title = QLabel("📤  OUTPUT")
        title.setStyleSheet("color:#89b4fa; font-size:12px; font-weight:bold;")
        hbox.addWidget(title)
        hbox.addStretch()
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#6c7086;border:none;"
            "font-size:11px;padding:2px 8px;}"
            "QPushButton:hover{color:#cdd6f4;}"
        )
        clear_btn.clicked.connect(self._clear_output)
        hbox.addWidget(clear_btn)
        layout.addWidget(hdr)

        self._output_area = QPlainTextEdit()
        self._output_area.setReadOnly(True)
        self._output_area.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {OUTPUT_BG};
                color: {OUTPUT_FG};
                border: none;
                padding: 8px;
                font-family: "JetBrains Mono","Fira Code","Consolas","Courier New",monospace;
                font-size: 12px;
            }}
        """)
        # Prevent UI freeze from huge output
        self._output_area.document().setMaximumBlockCount(5000)
        layout.addWidget(self._output_area)

        return panel

    def _make_dsa_feedback_panel(self) -> QWidget:
        """Build the DSA AI feedback bottom panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setFixedHeight(34)
        hdr.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #1a1a2e, stop:1 #1e1e2e);"
            "border-bottom: 1px solid #313244;"
        )
        hbox = QHBoxLayout(hdr)
        hbox.setContentsMargins(10, 0, 10, 0)
        title_lbl = QLabel("🎯  DSA AI FEEDBACK")
        title_lbl.setStyleSheet("color:#cba6f7; font-size:12px; font-weight:bold;")
        hbox.addWidget(title_lbl)
        hbox.addStretch()
        clear_fb = QPushButton("Clear")
        clear_fb.setStyleSheet(
            "QPushButton{background:transparent;color:#6c7086;border:none;"
            "font-size:11px;padding:2px 8px;}"
            "QPushButton:hover{color:#cdd6f4;}"
        )
        clear_fb.clicked.connect(lambda: self._dsa_feedback_area.clear())
        hbox.addWidget(clear_fb)
        layout.addWidget(hdr)

        self._dsa_feedback_area = QPlainTextEdit()
        self._dsa_feedback_area.setReadOnly(True)
        self._dsa_feedback_area.setStyleSheet(
            "QPlainTextEdit {"
            "  background:#0d0d1a; color:#cdd6f4; border:none; padding:10px;"
            "  font-family:'JetBrains Mono','Fira Code','Consolas',monospace;"
            "  font-size:12px; line-height:1.5;"
            "}"
        )
        self._dsa_feedback_area.document().setMaximumBlockCount(2000)
        self._dsa_feedback_area.setPlaceholderText(
            "Open a DSA question and click '🎯 Check Solution' to see AI feedback here."
        )
        layout.addWidget(self._dsa_feedback_area)
        return panel

    # ── DSA Practice Actions ──────────────────────────────────────────────────

    def _dsa_toggle_sidebar(self) -> None:
        """Show/hide the DSA sidebar panel."""
        if self._dsa_panel is None:
            return
        visible = not self._dsa_panel.isVisible()
        self._dsa_panel.setVisible(visible)
        if visible:
            sizes = self._h_splitter.sizes()
            if sizes[0] < 100:
                self._h_splitter.setSizes([280, max(sizes[1], 800)])
            self._dsa_panel.refresh()
            self._set_status("DSA sidebar opened")
        else:
            self._set_status("DSA sidebar closed")

    def _dsa_refresh(self) -> None:
        if self._dsa_panel is not None:
            self._dsa_panel.refresh()
            self._set_status("DSA questions refreshed")

    def _chatbot_toggle(self) -> None:
        """Show/hide the live chatbot panel (right side)."""
        if self._chatbot_panel is None:
            return
        visible = not self._chatbot_panel.isVisible()
        self._chatbot_panel.setVisible(visible)
        # Sync toolbar button checked state
        if hasattr(self, "_chatbot_btn") and self._chatbot_btn is not None:
            self._chatbot_btn.setChecked(visible)
        if visible:
            sizes = self._h_splitter.sizes()
            # Ensure chatbot gets ~320px; shrink editor slightly
            total = sum(sizes)
            chat_w = 320
            dsa_w  = sizes[0] if len(sizes) > 0 else 0
            ed_w   = max(total - dsa_w - chat_w, 400)
            self._h_splitter.setSizes([dsa_w, ed_w, chat_w])
            # Push API key + current tab context
            api_key = (
                self._settings.get("groq_api_key", "").strip()
                or self._settings.get("gemini_api_key", "").strip()
            )
            self._chatbot_panel.set_api_key(api_key)
            self._chatbot_sync_context()
            self._set_status("💬 Chatbot opened (Ctrl+Shift+I to close)")
        else:
            self._set_status("💬 Chatbot closed")

    def _chatbot_sync_context(self) -> None:
        """Push current editor tab content to the chatbot panel."""
        if self._chatbot_panel is None or not self._chatbot_panel.isVisible():
            return
        editor = self._current_editor()
        state  = self._current_state()
        if editor and state:
            code = editor.toPlainText() if hasattr(editor, "toPlainText") else ""
            fname = state.file_path.name if getattr(state, "file_path", None) else state.display_title
            lang  = state.language
            self._chatbot_panel.update_context(code, fname, lang)
        else:
            self._chatbot_panel.update_context("", "", "")

    def _chatbot_insert_to_editor(self, code: str, lang: str = "") -> None:
        """Insert AI-generated code into the active editor tab."""
        editor = self._current_editor()
        if editor is None:
            self._new_tab()
            editor = self._current_editor()
        if editor is None:
            return
        if hasattr(editor, "set_text"):
            editor.set_text(code)
        elif hasattr(editor, "setPlainText"):
            editor.setPlainText(code)

        # Switch language if valid
        if lang:
            for known in LANGUAGES:
                if known.lower() == lang.lower():
                    self._on_language_changed(known)
                    self._lang_combo.blockSignals(True)
                    self._lang_combo.setCurrentText(known)
                    self._lang_combo.blockSignals(False)
                    break
        self._set_status("💬 Code inserted from AI Chatbot into editor")

    def _chatbot_insert_and_run(self, code: str, lang: str = "") -> None:
        """Insert AI code into editor and run it immediately."""
        self._chatbot_insert_to_editor(code, lang)
        self._run_code()

    def _chatbot_run_terminal_command(self, cmd: str) -> None:
        """Execute a shell command from chatbot in the integrated terminal."""
        self._show_terminal_panel()
        lines = [line.strip() for line in cmd.strip().splitlines() if line.strip() and not line.strip().startswith("#")]
        for line in lines:
            self._on_terminal_input_submitted(line)
        self._set_status(f"⚡ Terminal executed: {cmd.strip()[:40]}")

    def _dsa_open_question(self, question: "Question") -> None:  # type: ignore[name-defined]
        """Open a DSA question in a new editor tab."""
        if not _HAS_DSA:
            return

        lang = self._lang_combo.currentText()
        # Prefer a supported DSA language
        if lang not in DSA_LANGS:
            lang = "Python"

        # Check for saved solution
        try:
            saved = get_solution(question.id)
        except Exception:
            saved = None

        saved_code = saved.code if saved else ""
        content = make_full_editor_content(question, lang, saved_code)

        # Open in a new tab
        tab_title = f"[DSA] {question.title}"
        idx = self._new_tab(
            title=tab_title,
            language=lang,
            code=content,
        )
        container = self._tab_widget.widget(idx)
        if container:
            st = self._tab_states.get(id(container))
            if st:
                st.dsa_question = question

        # Store active question state
        self._active_dsa_question = question
        self._dsa_submit_btn.setVisible(True)

        self._lang_combo.blockSignals(True)
        self._lang_combo.setCurrentText(lang)
        self._lang_combo.blockSignals(False)

        # Switch to the new tab
        self._tab_widget.setCurrentIndex(idx)

        if saved and saved.solved:
            self._set_status(
                f"✅ [{question.difficulty}] {question.title} — saved solution loaded"
            )
        else:
            self._set_status(
                f"🧩 [{question.difficulty}] {question.title} — write your solution!"
            )

        # Show DSA feedback tab
        self._show_dsa_feedback_tab()
        self._dsa_feedback_area.setPlainText(
            f"📋  {question.title}\n"
            f"{'─'*60}\n"
            f"Topic:       {question.topic}\n"
            f"Difficulty:  {question.difficulty}\n"
            f"Source:      {question.source}\n"
            f"LeetCode:    {'#' + str(question.lc_number) if question.lc_number else 'N/A'}\n"
            f"Time req:    {question.time_complexity}\n"
            f"Space req:   {question.space_complexity}\n"
            f"{'─'*60}\n"
            f"{'✅ Solved previously!' if (saved and saved.solved) else '⏳ Not yet solved — write your solution and click 🎯 Check Solution'}\n"
        )

    def _dsa_check_solution(self) -> None:
        """Send current editor code + question to Groq for AI checking."""
        if not _HAS_DSA:
            return
        if self._active_dsa_question is None:
            self._set_status("⚠ Open a DSA question first (use the 🧩 DSA sidebar)")
            return
        if self._dsa_checking:
            self._set_status("⚠ Already checking — please wait…")
            return

        api_key: str = (
            self._settings.get("groq_api_key", "").strip()
            or self._settings.get("gemini_api_key", "").strip()
        )
        if not api_key:
            QMessageBox.warning(
                self,
                "No API Key",
                "Please add your Groq API key in Settings → Preferences.\n"
                "Get a free key at https://console.groq.com",
            )
            return

        editor = self._current_editor()
        if editor is None:
            return

        # Strip the comment header — everything before the first non-comment line
        full_code = editor.toPlainText()
        lang = self._lang_combo.currentText()
        user_code = _extract_user_code(full_code, lang)

        if not user_code.strip():
            self._set_status("⚠ No solution code found — write your code below the comment block!")
            return

        q = self._active_dsa_question
        self._dsa_checking = True
        self._dsa_submit_btn.setEnabled(False)
        self._show_dsa_feedback_tab()
        self._dsa_feedback_area.setPlainText(
            f"⏳ Checking your {lang} solution for:\n"
            f"   {q.title}\n\n"
            f"Sending to Groq AI… please wait (up to 30 s)…"
        )
        self._set_status(f"🎯 Checking solution for {q.title}…")

        # Wire callbacks via Qt signal bridge (thread-safe)
        from PySide6.QtCore import QObject, Signal as _Sig

        class _Bridge(QObject):
            success = _Sig(object)
            error   = _Sig(str)

        bridge = _Bridge(self)
        bridge.success.connect(lambda r: self._dsa_on_check_done(r))
        bridge.error.connect(lambda e: self._dsa_on_check_error(e))

        check_solution_async(
            question_title=q.title,
            problem_statement=q.problem_statement,
            constraints=q.constraints,
            req_time=q.time_complexity,
            req_space=q.space_complexity,
            language=lang,
            code=user_code,
            api_key=api_key,
            on_success=bridge.success.emit,
            on_error=bridge.error.emit,
        )

    def _dsa_on_check_done(self, result: "CheckResult") -> None:  # type: ignore[name-defined]
        """Handle AI check result on main thread."""
        self._dsa_checking = False
        self._dsa_submit_btn.setEnabled(True)
        q = self._active_dsa_question
        if q is None:
            return

        if result.verdict == "correct":
            lines = [
                f"✅  CORRECT SOLUTION — {q.title}",
                "=" * 60,
                f"  {result.message}",
                "",
                "  Complexity Analysis:",
                f"  {result.complexity_note}",
                "",
                "━" * 60,
                "  🎉 Great work! Your solution is accepted.",
            ]
            self._dsa_feedback_area.setPlainText("\n".join(lines))
            self._set_status(f"✅ Correct! {q.title}")

            # Offer to save
            self._dsa_offer_save(q)

        else:
            issues_txt  = "\n".join(f"  • {i}" for i in result.issues) or "  (no specific issues listed)"
            edges_txt   = "\n".join(f"  • {e}" for e in result.edge_cases) or "  (none listed)"
            complexity  = "✅ Meets requirements" if result.complexity_ok else "⚠ Does NOT meet requirements"

            lines = [
                f"❌  INCORRECT SOLUTION — {q.title}",
                "=" * 60,
                f"  {result.message}",
                "",
                "  Issues:",
                issues_txt,
                "",
                "  Failing Edge Cases:",
                edges_txt,
                "",
                f"  Complexity: {complexity}",
                f"  {result.complexity_note}",
                "",
                "━" * 60,
                "  💡 Hint  (not the full solution):",
                f"  {result.hint if result.hint else 'Keep thinking — you can do it!'}",
            ]
            self._dsa_feedback_area.setPlainText("\n".join(lines))
            self._set_status(f"❌ Needs work — {q.title}")

    def _dsa_on_check_error(self, msg: str) -> None:
        self._dsa_checking = False
        self._dsa_submit_btn.setEnabled(True)
        self._dsa_feedback_area.setPlainText(
            f"⚠  Error checking solution:\n\n{msg}\n\n"
            f"Check your API key in Settings or your internet connection."
        )
        self._set_status(f"⚠ Check failed: {msg[:60]}")

    def _dsa_offer_save(self, question: "Question") -> None:  # type: ignore[name-defined]
        """Popup asking if the user wants to save their correct solution."""
        editor = self._current_editor()
        if editor is None:
            return
        lang = self._lang_combo.currentText()
        full_code = editor.toPlainText()
        user_code = _extract_user_code(full_code, lang)

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Solution Correct!")
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setText("Your solution is correct! Do you want to save this code with the question?")
        save_btn = msg_box.addButton("Save", QMessageBox.ButtonRole.AcceptRole)
        skip_btn = msg_box.addButton("Skip", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(save_btn)
        msg_box.exec()

        if msg_box.clickedButton() == save_btn:
            try:
                save_solution(question.id, lang, user_code, solved=True)
                if self._dsa_panel is not None:
                    self._dsa_panel.mark_solved(question.id)
                self._set_status(f"💾 Solution saved — {question.title}")
                self._dsa_feedback_area.appendPlainText(
                    "\n\n✅ Solution saved to local storage!"
                )
            except Exception as e:
                QMessageBox.warning(self, "Save Error", f"Could not save solution:\n{e}")

    def _show_dsa_feedback_tab(self) -> None:
        """Switch the bottom panel to the DSA feedback tab."""
        for i in range(self._bottom_tabs.count()):
            if "DSA" in self._bottom_tabs.tabText(i):
                self._bottom_tabs.setCurrentIndex(i)
                if self._v_splitter.sizes()[1] < 80:
                    self._v_splitter.setSizes([520, 220])
                return


    def _build_status_bar(self) -> None:
        sb = QStatusBar()
        self.setStatusBar(sb)


        self._status_lang    = QLabel("Python")
        self._status_cursor  = QLabel("Ln 1, Col 1")
        self._status_spaces  = QLabel("Spaces: 4")
        self._status_enc     = QLabel("UTF-8")
        self._status_ready   = QLabel("Ready")
        self._status_ready.setStyleSheet("color:#a6e3a1; font-weight:600;")

        for w in (
            self._status_ready,
            self._sep(), self._status_lang,
            self._sep(), self._status_cursor,
            self._sep(), self._status_spaces,
            self._sep(), self._status_enc,
        ):
            sb.addPermanentWidget(w)

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color:#313244;")
        return sep

    # ── Tab management ────────────────────────────────────────────────────────

    def _generate_untitled_title(self) -> str:
        existing_titles = {state.title for state in self._tab_states.values()}
        if "Untitled" not in existing_titles:
            return "Untitled"
        i = 1
        while f"Untitled {i}" in existing_titles:
            i += 1
        return f"Untitled {i}"

    def _new_tab(
        self,
        title: str | None = None,
        language: str | None = None,
        file_path: Path | None = None,
        code: str | None = None,
    ) -> int:
        if title is None:
            title = self._generate_untitled_title()
        lang = language or self._lang_combo.currentText()
        state = TabState(title=title, language=lang, file_path=file_path)

        container = QWidget()
        container.setStyleSheet("background:#1e1e2e;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if _HAS_CUSTOM_EDITOR:
            editor = make_editor(container)
        else:
            editor = self._fallback_editor(container)

        layout.addWidget(editor)

        # Set initial code — block modified signal during init
        editor.blockSignals(True)
        initial = code if code is not None else DEFAULT_CODE.get(lang, "")
        editor.set_text(initial)
        editor.blockSignals(False)

        # Connect editor signals AFTER setting initial text
        if hasattr(editor, "run_requested"):
            editor.run_requested.connect(self._run_code)
        if hasattr(editor, "zoom_in_requested"):
            editor.zoom_in_requested.connect(self._zoom_in)
        if hasattr(editor, "zoom_out_requested"):
            editor.zoom_out_requested.connect(self._zoom_out)
        if hasattr(editor, "zoom_reset_requested"):
            editor.zoom_reset_requested.connect(self._zoom_reset)
        editor.textChanged.connect(
            lambda: self._on_editor_modified(id(container))
        )
        # Live-sync chatbot context when editor content changes
        editor.textChanged.connect(self._chatbot_sync_context)
        if hasattr(editor, "cursor_position_changed"):
            editor.cursor_position_changed.connect(self._update_cursor_status)
        elif hasattr(editor, "cursorPositionChanged"):
            editor.cursorPositionChanged.connect(
                lambda: self._update_cursor_from_editor(editor)
            )

        # Set language for syntax highlighting
        if hasattr(editor, "set_language"):
            editor.set_language(lang)

        # Apply current settings to editor
        if hasattr(editor, "set_font_size"):
            editor.set_font_size(self._settings.get("font_size", 14))
        if hasattr(editor, "set_tab_size"):
            editor.set_tab_size(self._settings.get("tab_size", 4))
        if hasattr(editor, "set_word_wrap"):
            editor.set_word_wrap(self._settings.get("word_wrap", False))

        cid = id(container)
        self._tab_states[cid] = state
        container._editor_widget = editor  # type: ignore[attr-defined]

        idx = self._tab_widget.addTab(container, state.display_title)
        self._tab_widget.setCurrentIndex(idx)
        return idx

    def _fallback_editor(self, parent: QWidget) -> QPlainTextEdit:
        """Minimal editor if custom editor is unavailable."""
        ed = QPlainTextEdit(parent)
        ed.setStyleSheet(
            f"background:#1e1e2e; color:#cdd6f4; border:none;"
            f" font-family:monospace; font-size:14px;"
        )
        ed.get_text = ed.toPlainText          # type: ignore[attr-defined]
        ed.set_text = ed.setPlainText         # type: ignore[attr-defined]
        ed.set_language = lambda _: None      # type: ignore[attr-defined]
        ed.set_font_size = lambda s: (
            ed.setStyleSheet(
                f"background:#1e1e2e; color:#cdd6f4; border:none;"
                f" font-family:monospace; font-size:{s}pt;"
            ),
            ed.setFont(QFont("monospace", s))
        )  # type: ignore[attr-defined]
        ed.set_tab_size = lambda _: None      # type: ignore[attr-defined]
        ed.set_word_wrap = lambda _: None     # type: ignore[attr-defined]
        return ed

    def _current_container(self) -> QWidget | None:
        return self._tab_widget.currentWidget()

    def _current_editor(self):
        container = self._current_container()
        if container is None:
            return None
        return getattr(container, "_editor_widget", None)

    def _current_state(self) -> TabState | None:
        container = self._current_container()
        if container is None:
            return None
        return self._tab_states.get(id(container))

    def _close_tab(self, index: int) -> None:
        container = self._tab_widget.widget(index)
        if container is None:
            return
        cid = id(container)
        state = self._tab_states.get(cid)
        if state and state.is_modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                f'"{state.title}" has unsaved changes.\nSave before closing?',
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Save:
                self._tab_widget.setCurrentIndex(index)
                if not self._save_file():
                    return
        self._tab_states.pop(cid, None)
        self._tab_widget.removeTab(index)
        if self._tab_widget.count() == 0:
            self._new_tab()

    def _close_current_tab(self) -> None:
        idx = self._tab_widget.currentIndex()
        if idx >= 0:
            self._close_tab(idx)

    def _next_tab(self) -> None:
        n = self._tab_widget.count()
        if n > 1:
            self._tab_widget.setCurrentIndex((self._tab_widget.currentIndex() + 1) % n)

    def _prev_tab(self) -> None:
        n = self._tab_widget.count()
        if n > 1:
            self._tab_widget.setCurrentIndex((self._tab_widget.currentIndex() - 1) % n)

    def _on_tab_changed(self, _index: int) -> None:
        state = self._current_state()
        if state:
            self._lang_combo.blockSignals(True)
            self._lang_combo.setCurrentText(state.language)
            self._lang_combo.blockSignals(False)
            self._update_language_ui(state.language)
            self._update_status_bar()
            self._prev_language = state.language  # sync so next switch knows the starting lang
            self._active_dsa_question = getattr(state, "dsa_question", None)
            if hasattr(self, "_dsa_submit_btn"):
                self._dsa_submit_btn.setVisible(self._active_dsa_question is not None)
        # Sync chatbot context whenever tab changes
        self._chatbot_sync_context()

    def _on_editor_modified(self, cid: int) -> None:
        state = self._tab_states.get(cid)
        if state and not state.is_modified:
            state.is_modified = True
            # Find tab index by container id
            for i in range(self._tab_widget.count()):
                w = self._tab_widget.widget(i)
                if w and id(w) == cid:
                    self._tab_widget.setTabText(i, state.display_title)
                    break

    # ── Language management ───────────────────────────────────────────────────

    def _on_language_changed(self, language: str) -> None:
        from_lang = self._prev_language  # language BEFORE the switch
        self._prev_language = language   # update for next switch

        state = self._current_state()
        if state:
            state.language = language
        editor = self._current_editor()
        if editor and hasattr(editor, "set_language"):
            editor.set_language(language)
        self._update_language_ui(language)
        self._update_status_bar()

        # ── AI Transpilation ──────────────────────────────────────────────────
        api_key: str = (
            self._settings.get("groq_api_key", "").strip()
            or self._settings.get("gemini_api_key", "").strip()
        )
        if (
            api_key
            and editor is not None
            and not self._transpile_in_progress
            and can_transpile(from_lang, language)
        ):
            code = editor.toPlainText().strip()
            if code:
                self._start_transpilation(editor, code, from_lang, language, api_key)

    def _start_transpilation(self, editor, code: str, from_lang: str, to_lang: str, api_key: str) -> None:
        """Kick off a background transpilation and wire up result callbacks."""
        from PySide6.QtCore import QObject, Signal as _Signal

        class _Bridge(QObject):
            """Tiny signal bridge — lives on the main thread, receives from worker."""
            success = _Signal(str)
            error   = _Signal(str)

        bridge = _Bridge(self)  # parent=self → stays alive while self does
        bridge.success.connect(lambda converted: self._apply_transpiled_code(converted, editor))
        bridge.error.connect(self._transpile_error)

        self._transpile_in_progress = True
        self._set_status(f"⚡ Translating {from_lang} → {to_lang}…")

        transpile_async(
            code, from_lang, to_lang, api_key,
            on_success=bridge.success.emit,
            on_error=bridge.error.emit,
        )

    def _apply_transpiled_code(self, converted: str, editor) -> None:
        """Called on the main thread after successful transpilation."""
        self._transpile_in_progress = False
        try:
            if editor is None:
                return
            cursor = editor.textCursor()
            cursor.select(cursor.SelectionType.Document)
            cursor.insertText(converted)
            editor.setTextCursor(cursor)
            self._set_status("✅ Code translated successfully")
        except Exception:  # noqa: BLE001
            self._set_status("⚠ Could not apply translated code")

    def _transpile_error(self, msg: str) -> None:
        """Called on the main thread after a transpilation failure."""
        self._transpile_in_progress = False
        self._set_status(f"⚠ Transpile error: {msg[:80]}")

    def _update_language_ui(self, language: str) -> None:
        is_web = language in ("HTML", "CSS")
        is_sql = language == "SQL"
        self._preview_btn.setVisible(is_web)
        if hasattr(self, "_browser_btn"):
            self._browser_btn.setVisible(is_web)
        self._run_btn.setVisible(True)
        self._run_btn.setText("🌐  PREVIEW" if is_web else "▶  RUN")
        if hasattr(self, "_sql_db_label"):
            self._sql_db_label.setVisible(is_sql)
        if hasattr(self, "_sql_db_btn"):
            self._sql_db_btn.setVisible(is_sql)

    # ── File operations ───────────────────────────────────────────────────────

    def _open_file(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            str(Path.home()),
            "All Supported (*.py *.c *.cpp *.cc *.cxx *.java *.js *.html *.htm *.css *.sql *.db *.sqlite *.sqlite3);;"
            "Python (*.py);;C (*.c);;C++ (*.cpp *.cc *.cxx);;Java (*.java);;"
            "JavaScript (*.js);;HTML (*.html *.htm);;CSS (*.css);;SQL (*.sql);;"
            "SQLite DB (*.db *.sqlite *.sqlite3);;All Files (*)",
        )
        if path_str:
            self._open_file_path(Path(path_str))

    def _open_file_path(self, path: Path) -> None:
        try:
            code = path.read_text(encoding="utf-8")
        except OSError as e:
            QMessageBox.critical(self, "Open Error", f"Could not open file:\n{e}")
            return
        lang = detect_language(path) or "Python"
        self._new_tab(title=path.name, language=lang, file_path=path, code=code)
        state = self._current_state()
        if state:
            state.is_modified = False
            state.file_path = path
            state.title = path.name
            idx = self._tab_widget.currentIndex()
            self._tab_widget.setTabText(idx, state.display_title)
        add_recent_file(str(path))
        self._refresh_recent_menu()

    def _save_file(self) -> bool:
        state = self._current_state()
        if state and state.file_path:
            return self._write_file(state.file_path)
        return self._save_file_as()

    def _save_file_as(self) -> bool:
        state = self._current_state()
        lang = state.language if state else "Python"
        ext = LANGUAGE_EXTENSIONS.get(lang, ".txt")
        default_name = (state.title if state and state.title != "Untitled" else f"Untitled{ext}")
        if not default_name.endswith(ext):
            default_name += ext
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            str(Path.home() / default_name),
            "All Files (*)",
        )
        if not path_str:
            return False
        path = Path(path_str)
        if self._write_file(path):
            if state:
                state.file_path = path
                state.title = path.name
                idx = self._tab_widget.currentIndex()
                self._tab_widget.setTabText(idx, state.display_title)
            add_recent_file(str(path))
            self._refresh_recent_menu()
            return True
        return False

    def _write_file(self, path: Path) -> bool:
        editor = self._current_editor()
        if not editor:
            return False
        code = editor.get_text()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(code, encoding="utf-8")
        except OSError as e:
            QMessageBox.critical(self, "Save Error", f"Could not save file:\n{e}")
            return False
        state = self._current_state()
        if state:
            state.is_modified = False
            idx = self._tab_widget.currentIndex()
            self._tab_widget.setTabText(idx, state.display_title)
        self._set_status(f"Saved: {path.name}")
        return True

    def _refresh_recent_menu(self) -> None:
        self._recent_menu.clear()
        files = load_recent_files()
        if not files:
            a = QAction("(No recent files)", self)
            a.setEnabled(False)
            self._recent_menu.addAction(a)
            return
        for fp in files[:15]:
            action = QAction(Path(fp).name + f"  —  {fp}", self)
            action.triggered.connect(
                lambda checked=False, p=fp: self._open_file_path(Path(p))
            )
            self._recent_menu.addAction(action)

    # ── Edit operations ───────────────────────────────────────────────────────

    def _undo(self) -> None:
        e = self._current_editor()
        if e and hasattr(e, "undo"):
            e.undo()

    def _redo(self) -> None:
        e = self._current_editor()
        if e and hasattr(e, "redo"):
            e.redo()

    def _cut(self) -> None:
        e = self._current_editor()
        if e and hasattr(e, "cut"):
            e.cut()

    def _copy(self) -> None:
        e = self._current_editor()
        if e and hasattr(e, "copy"):
            e.copy()

    def _paste(self) -> None:
        e = self._current_editor()
        if e and hasattr(e, "paste"):
            e.paste()

    def _select_all(self) -> None:
        e = self._current_editor()
        if e and hasattr(e, "selectAll"):
            e.selectAll()

    def _show_find(self) -> None:
        self._get_or_create_find_dialog().open_with_focus()

    def _show_find_replace(self) -> None:
        self._get_or_create_find_dialog().open_with_focus()

    def _get_or_create_find_dialog(self) -> FindReplaceDialog:
        if self._find_dialog is None or not self._find_dialog.isVisible():
            self._find_dialog = FindReplaceDialog(self._current_editor, self)
        return self._find_dialog

    # ── Zoom ─────────────────────────────────────────────────────────────────

    def _zoom_in(self) -> None:
        self._settings["font_size"] = min(self._settings.get("font_size", 14) + 2, 40)
        save_settings(self._settings)
        self._apply_settings()
        self.statusBar().showMessage(f"🔍 Zoom: {self._settings['font_size']}pt", 1500)

    def _zoom_out(self) -> None:
        self._settings["font_size"] = max(self._settings.get("font_size", 14) - 2, 8)
        save_settings(self._settings)
        self._apply_settings()
        self.statusBar().showMessage(f"🔍 Zoom: {self._settings['font_size']}pt", 1500)

    def _zoom_reset(self) -> None:
        self._settings["font_size"] = 14
        save_settings(self._settings)
        self._apply_settings()
        self.statusBar().showMessage("🔍 Zoom Reset: 14pt", 1500)

    # ── Run / Stop ────────────────────────────────────────────────────────────

    def _run_code(self) -> None:
        state = self._current_state()
        if state is None:
            return
        editor = self._current_editor()
        if editor is None:
            return

        # HTML/CSS → preview and browser execution
        if state.language in ("HTML", "CSS"):
            self._show_preview()
            self._open_in_browser()
            return

        # SQL → SQLite execution
        if state.language == "SQL":
            self._run_sql()
            return

        code = editor.get_text().strip()
        if not code:
            self._clear_output()
            self._append_output("⚠  No code to run.\n", "#f9e2af")
            return

        # Check tools first
        missing = get_missing_tools(state.language)
        if missing:
            self._show_terminal_panel()
            self._term_output.clear()
            self._term_append(
                f"❌  Missing tools: {', '.join(missing)}\n"
                f"    {_install_hint(state.language)}\n",
                "#f38ba8",
            )
            return

        # Already running?
        if self._runner_thread and self._runner_thread.isRunning():
            self._runner_thread.wait(1000)
            if self._runner_thread.isRunning():
                return

        timeout = self._settings.get("execution_timeout", 10)

        self._show_terminal_panel()
        self._term_output.clear()
        self._term_append(f"$ Run {state.language}\n\n", "#a6e3a1")
        self._set_diagnostics([])
        self._set_running_state(True)

        self._runner_thread = RunnerThread(self)
        self._runner_thread.configure(
            language=state.language,
            code=code,
            stdin_data="",
            timeout=timeout,
            saved_path=state.file_path,
        )
        self._runner_thread.started_signal.connect(self._on_run_started)
        self._runner_thread.stdout_signal.connect(self._on_stdout_chunk)
        self._runner_thread.stderr_signal.connect(self._on_stderr_chunk)
        self._runner_thread.status_signal.connect(self._on_runner_status)
        self._runner_thread.finished_signal.connect(self._on_run_finished)
        self._runner_thread.start()

    def _stop_execution(self) -> None:
        if self._runner_thread and self._runner_thread.isRunning():
            self._runner_thread.stop_execution()
        elif hasattr(self, "_term_thread") and self._term_thread.isRunning():
            self._term_thread.stop()
        else:
            self._set_running_state(False)
            self._set_status("Ready")

    def _send_eof(self) -> None:
        if self._runner_thread and self._runner_thread.isRunning():
            self._runner_thread.close_stdin()
            self._term_append("^D\n", "#f9e2af")
            self._set_status("Sent EOF to process")

    def _set_running_state(self, running: bool) -> None:
        self._run_btn.setEnabled(not running)
        self._stop_btn.setEnabled(running)
        if hasattr(self, "_term_stop_btn"):
            self._term_stop_btn.setEnabled(running or self._term_running)
        if running:
            self._set_status("Running…")

    def _on_run_started(self) -> None:
        self._set_status("Running…")

    def _on_stdout_chunk(self, chunk: str) -> None:
        self._term_append(chunk, "#cdd6f4")

    def _on_stderr_chunk(self, chunk: str) -> None:
        self._term_append(chunk, "#f38ba8")

    def _on_runner_status(self, msg: str) -> None:
        self._set_status(msg)
        if msg == "Running…":
            if hasattr(self, "_term_console"):
                self._term_console.setFocus()
            elif hasattr(self, "_term_input"):
                self._term_input.setFocus()

    def _on_run_finished(self, result) -> None:
        # Always restore UI
        self._set_running_state(False)

        if result.error_message == "PREVIEW":
            self._show_preview()
            self._set_status("Preview rendered.")
            return

        if result.cancelled:
            self._term_append("\n⏹  Execution stopped by user.\n", "#f9e2af")
            self._set_status("Stopped.")
            self._reset_terminal_input()
            return

        if result.error_message:
            self._term_append(f"\n❌  {result.error_message}\n", "#f38ba8")
            self._set_status("Error.")
            self._reset_terminal_input()
            return

        # ── Compile errors ──
        if result.is_compile_error:
            self._term_append("\n── COMPILE ERROR ──\n", "#fab387")
            if result.stderr:
                self._term_append(result.stderr, "#f38ba8")
            if result.stdout:
                self._term_append(result.stdout, "#f38ba8")
            
            diagnostics = parse_diagnostics(
                (result.stderr or "") + "\n" + (result.stdout or ""),
                self._current_state().language if self._current_state() else ""
            )
            self._set_diagnostics(diagnostics)
            self._bottom_tabs.setCurrentWidget(self._problems_panel)
            self._set_status("Compile error")
            self._reset_terminal_input()
            return

        elif result.compiler_output:
            diagnostics = parse_diagnostics(
                result.compiler_output,
                self._current_state().language if self._current_state() else ""
            )
            if diagnostics:
                self._set_diagnostics(diagnostics)

        if result.timed_out:
            self._term_append(
                f"\n⏱  Timed out after {self._settings.get('execution_timeout', 10)}s.\n",
                "#f9e2af",
            )

        # Status bar update
        if result.timed_out:
            status_text = "Timed out"
            status_color = "#f9e2af"
        elif result.exit_code == 0:
            status_text = "Finished ✓"
            status_color = "#a6e3a1"
        else:
            display_exit = 128 - result.exit_code if result.exit_code < 0 else result.exit_code
            status_text = f"Exit code: {display_exit}"
            status_color = "#f38ba8"

        self._set_status(status_text)
        if not result.is_compile_error:
            display_exit = 128 - result.exit_code if result.exit_code < 0 else result.exit_code
            
            # Runtime error description (e.g. segfault)
            if display_exit in (139, 11):
                self._term_append("\n❌  Runtime Error: Segmentation fault (SIGSEGV)\n", "#f38ba8")
            elif display_exit in (134, 6):
                self._term_append("\n❌  Runtime Error: Aborted (SIGABRT)\n", "#f38ba8")
            elif display_exit in (136, 8):
                self._term_append("\n❌  Runtime Error: Floating point exception / Division by zero\n", "#f38ba8")
                
            self._term_append(
                f"\nProcess exited with code {display_exit}  ·  Time: {result.elapsed_time:.3f}s\n",
                status_color,
            )
        self._reset_terminal_input()


    def _reset_terminal_input(self) -> None:
        pass

    def _append_output(self, text: str, color: str = OUTPUT_FG) -> None:
        cursor = self._output_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = cursor.charFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        self._output_area.setTextCursor(cursor)
        self._output_area.ensureCursorVisible()

    def _clear_output(self) -> None:
        self._output_area.clear()



    def _set_diagnostics(self, diagnostics: list[Diagnostic]) -> None:
        self._problems_list.clear()
        for diagnostic in diagnostics:
            location = ""
            if diagnostic.line:
                filename = Path(diagnostic.file).name if diagnostic.file else "main"
                location = f"{filename}:{diagnostic.line}"
                if diagnostic.column:
                    location += f":{diagnostic.column}"
                location += "  "

            icon = "🔴" if diagnostic.severity == "error" else ("🟡" if diagnostic.severity == "warning" else "🔵")
            color = "#f38ba8" if diagnostic.severity == "error" else ("#f9e2af" if diagnostic.severity == "warning" else "#89b4fa")

            item = QListWidgetItem(f"{icon}  {diagnostic.severity.upper()}  ·  {location}{diagnostic.message}")
            item.setData(Qt.ItemDataRole.UserRole, diagnostic)
            item.setForeground(QColor(color))
            self._problems_list.addItem(item)
        self._bottom_tabs.setTabText(0, f"PROBLEMS  {len(diagnostics)}")

    def _go_to_diagnostic(self, item: QListWidgetItem) -> None:
        diagnostic = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(diagnostic, Diagnostic) or not diagnostic.line:
            return

        # Find matching open tab if diagnostic specifies a file
        if diagnostic.file:
            diag_file_path = Path(diagnostic.file)
            for idx in range(self._tab_widget.count()):
                container = self._tab_widget.widget(idx)
                cid = id(container)
                state = self._tab_states.get(cid)
                if state:
                    if state.file_path and state.file_path.name == diag_file_path.name:
                        self._tab_widget.setCurrentIndex(idx)
                        break
                    elif state.title == diag_file_path.name or state.display_title == diag_file_path.name:
                        self._tab_widget.setCurrentIndex(idx)
                        break

        editor = self._current_editor()
        if editor is None:
            return

        doc = editor.document()
        block = doc.findBlockByNumber(max(0, diagnostic.line - 1))
        if not block.isValid():
            return

        cursor = QTextCursor(block)
        col = max(0, (diagnostic.column or 1) - 1)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, col)
        if diagnostic.column and col < block.length() - 1:
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 1)

        editor.setTextCursor(cursor)
        editor.setFocus()
        editor.ensureCursorVisible()

    # ── Preview & Browser ─────────────────────────────────────────────────────

    def _open_in_browser(self) -> None:
        """Open the current HTML/CSS file directly in the user's default web browser."""
        state = self._current_state()
        editor = self._current_editor()
        if state is None or editor is None:
            return
        code = editor.get_text()
        from app.preview import open_in_default_browser
        try:
            path = open_in_default_browser(
                code,
                is_css=(state.language == "CSS"),
                file_path=state.file_path,
            )
            self._set_status(f"🌐 Running {state.language} in default browser")
            self._show_terminal_panel()
            self._term_output.clear()
            self._term_append(
                f"🌍  Launched in system default browser:\n    file://{path}\n"
                f"    Lines: {len(code.splitlines())}  ·  Bytes: {len(code)}\n\n",
                "#89b4fa",
            )
        except Exception as e:
            QMessageBox.warning(self, "Browser Error", f"Could not open browser:\n{e}")

    def _show_preview(self) -> None:
        state = self._current_state()
        editor = self._current_editor()
        if state is None or editor is None:
            return

        code = editor.get_text()

        # Create dialog ONCE — never recreate or reparent the PreviewPanel!
        if self._preview_dialog is None:
            # Use Window flag so it's a standalone window, not a modal child
            self._preview_dialog = QDialog(self, Qt.WindowType.Window)
            self._preview_dialog.setWindowTitle("HTML/CSS Live Preview — Nitin Editor")
            self._preview_dialog.resize(920, 640)
            # Never destroy on close — we reuse the same WebEngine widget
            self._preview_dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
            dlayout = QVBoxLayout(self._preview_dialog)
            dlayout.setContentsMargins(0, 0, 0, 0)
            try:
                self._preview_panel = PreviewPanel(self._preview_dialog)
                dlayout.addWidget(self._preview_panel)
            except Exception:
                # Fallback to direct default browser if widget creation fails
                self._preview_dialog = None
                self._open_in_browser()
                return

        if self._preview_panel is not None:
            try:
                if state.language == "HTML":
                    self._preview_panel.render_html(code, file_path=state.file_path)
                elif state.language == "CSS":
                    self._preview_panel.render_css_only(code)
            except Exception:
                pass

        self._preview_dialog.show()
        self._preview_dialog.raise_()
        self._preview_dialog.activateWindow()

    # ── Settings ──────────────────────────────────────────────────────────────

    def _show_settings(self) -> None:
        dialog = SettingsDialog(self._settings, self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()

    def _on_settings_changed(self, new_settings: dict) -> None:
        self._settings = new_settings
        save_settings(new_settings)
        self._apply_settings()

    def _apply_settings(self) -> None:
        theme = self._settings.get("theme", "dark")
        self.setStyleSheet(DARK_STYLE if theme == "dark" else "")

        font_size = self._settings.get("font_size", 14)
        tab_size  = self._settings.get("tab_size", 4)
        word_wrap = self._settings.get("word_wrap", False)

        for i in range(self._tab_widget.count()):
            container = self._tab_widget.widget(i)
            if container:
                editor = getattr(container, "_editor_widget", None)
                if editor:
                    for attr, val in (
                        ("set_font_size", font_size),
                        ("set_tab_size",  tab_size),
                        ("set_word_wrap", word_wrap),
                    ):
                        if hasattr(editor, attr):
                            getattr(editor, attr)(val)

        self._status_spaces.setText(f"Spaces: {tab_size}")
        self._update_status_bar()

        # Push Groq API key to chatbot panel
        if self._chatbot_panel is not None:
            api_key = (
                self._settings.get("groq_api_key", "").strip()
                or self._settings.get("gemini_api_key", "").strip()
            )
            self._chatbot_panel.set_api_key(api_key)

    # ── Status helpers ────────────────────────────────────────────────────────

    def _update_status_bar(self) -> None:
        state = self._current_state()
        if state:
            self._status_lang.setText(state.language)

    def _update_cursor_status(self, line: int, col: int) -> None:
        self._status_cursor.setText(f"Ln {line}, Col {col}")

    def _update_cursor_from_editor(self, editor) -> None:
        if hasattr(editor, "get_cursor_position"):
            line, col = editor.get_cursor_position()
            self._update_cursor_status(line, col)

    def _set_status(self, text: str) -> None:
        self._status_text = text
        self._status_ready.setText(text)

    # ── SQL execution ─────────────────────────────────────────────────────────

    def _run_sql(self) -> None:
        """Execute the current SQL tab contents using sqlite3 (built-in, no server needed)."""
        editor = self._current_editor()
        if editor is None:
            return
        sql = editor.get_text().strip()
        if not sql:
            self._show_terminal_panel()
            self._term_append("⚠  No SQL to execute.\n", "#f9e2af")
            return

        if self._runner_thread and self._runner_thread.isRunning():
            return

        db_path = self._sql_db_path  # None = temp db

        self._show_terminal_panel()
        self._term_output.clear()
        self._set_running_state(True)
        self._term_append("⚙  Executing SQL (SQLite)…\n\n", "#89b4fa")

        # Run in background thread using QThread to keep GUI responsive
        self._sql_thread = _SQLThread(sql, db_path, parent=self)
        self._sql_thread.result_ready.connect(self._on_sql_finished)
        self._sql_thread.start()

    def _on_sql_finished(self, result: SQLResult) -> None:
        self._set_running_state(False)
        if result.output:
            self._term_append(result.output, "#cdd6f4")
        if result.error:
            self._term_append(f"❌  {result.error}\n", "#f38ba8")
        if not result.success:
            message = result.error
            if not message and "SQL Error:" in result.output:
                message = result.output.split("SQL Error:", 1)[1].split("Statement:", 1)[0].strip()
            self._set_diagnostics([sql_diagnostic(message or "SQL error")])
            self._bottom_tabs.setCurrentWidget(self._problems_panel)
        status_text = "SQL OK ✓" if result.success else "SQL Error"
        status_color = "#a6e3a1" if result.success else "#f38ba8"
        self._set_status(status_text)
        self._term_append(
            f"\n{status_text}  ·  Statements: {result.statement_count}  ·  Time: {result.elapsed_time:.3f}s\n",
            status_color,
        )

    def _make_integrated_terminal_panel(self) -> QWidget:
        """One terminal stream for program I/O and optional shell commands."""
        panel = QWidget()
        panel.setStyleSheet("background:#11111b;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(34)
        header.setStyleSheet("background:#1a1a2e;border-bottom:1px solid #313244;")
        row = QHBoxLayout(header)
        row.setContentsMargins(10, 0, 8, 0)
        label = QLabel("⌨  TERMINAL")
        label.setStyleSheet("color:#89b4fa;font-size:12px;font-weight:bold;")
        row.addWidget(label)
        row.addStretch()
        self._term_os_combo = QComboBox()
        self._term_os_combo.addItems(["Linux", "macOS", "Windows"])
        self._term_os_combo.setCurrentText(self._settings.get("terminal_default_os", "Linux"))
        self._term_os_combo.setMaximumWidth(115)
        row.addWidget(self._term_os_combo)
        eof = QPushButton("EOF")
        eof.clicked.connect(self._send_eof)
        row.addWidget(eof)
        clear = QPushButton("Clear")
        clear.clicked.connect(lambda: self._term_console.clear_terminal())
        row.addWidget(clear)
        self._term_stop_btn = QPushButton("■ Stop")
        self._term_stop_btn.clicked.connect(self._stop_execution)
        self._term_stop_btn.setEnabled(False)
        row.addWidget(self._term_stop_btn)
        layout.addWidget(header)

        self._term_console = TerminalConsole()
        self._term_console.set_history(self._term_history)
        self._term_console.input_submitted.connect(self._on_terminal_input_submitted)
        self._term_console.interrupt_requested.connect(self._stop_execution)
        self._term_console.eof_requested.connect(self._send_eof)
        layout.addWidget(self._term_console)

        self._term_output = self._term_console
        self._term_input = _TermInputCompat(self._term_console)
        self._terminal_prompt = QLabel("$")
        return panel

    def _select_sql_db(self) -> None:
        """Open a dialog to choose a SQLite database file for SQL execution."""
        from PySide6.QtWidgets import QFileDialog
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Select SQLite Database",
            str(Path.home()),
            "SQLite Databases (*.db *.sqlite *.sqlite3);;All Files (*)",
        )
        if path_str:
            self._sql_db_path = Path(path_str)
            self._set_status(f"SQL DB: {self._sql_db_path.name}")
            if hasattr(self, "_sql_db_label"):
                self._sql_db_label.setText(f"DB: {self._sql_db_path.name}")
        else:
            self._sql_db_path = None
            if hasattr(self, "_sql_db_label"):
                self._sql_db_label.setText("DB: Temporary")

    # ── Terminal panel ────────────────────────────────────────────────────────

    def _show_terminal_panel(self) -> None:
        """Select the shared integrated terminal tab."""
        self._bottom_tabs.setCurrentWidget(self._terminal_panel_widget)
        if hasattr(self, "_term_console"):
            self._term_console.setFocus()
        elif hasattr(self, "_term_input"):
            self._term_input.setFocus()


    def _build_terminal_panel(self) -> None:
        """
        Build the terminal panel and insert it into the main vertical splitter
        as a third pane below the existing code editor and input/output panes.
        """
        from PySide6.QtWidgets import QTabWidget as QTW

        self._terminal_panel_widget = QWidget()
        self._terminal_panel_widget.setStyleSheet("background:#11111b;")
        tlay = QVBoxLayout(self._terminal_panel_widget)
        tlay.setContentsMargins(0, 0, 0, 0)
        tlay.setSpacing(0)

        # Header bar
        hdr = QWidget()
        hdr.setFixedHeight(34)
        hdr.setStyleSheet("background:#1a1a2e; border-bottom:1px solid #313244;")
        hbox = QHBoxLayout(hdr)
        hbox.setContentsMargins(10, 0, 8, 0)
        hbox.setSpacing(8)

        term_lbl = QLabel("\u2328  TERMINAL")
        term_lbl.setStyleSheet("color:#89b4fa; font-size:12px; font-weight:bold;")
        hbox.addWidget(term_lbl)

        hbox.addWidget(QLabel("  OS:"))
        self._term_os_combo = QComboBox()
        for os_name in ["Linux", "macOS", "Windows"]:
            self._term_os_combo.addItem(os_name)
        default_os = self._settings.get("terminal_default_os", "Linux")
        self._term_os_combo.setCurrentText(default_os)
        self._term_os_combo.setMaximumWidth(120)
        self._term_os_combo.setStyleSheet(
            "QComboBox{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
            "border-radius:4px;padding:2px 6px;font-size:11px;}"
            "QComboBox::drop-down{border:none;}"
        )
        hbox.addWidget(self._term_os_combo)

        hbox.addStretch()

        # SQL DB selector (shown when SQL tab is active)
        self._sql_db_label = QLabel("DB: Temporary")
        self._sql_db_label.setStyleSheet("color:#f9e2af; font-size:11px;")
        self._sql_db_label.setVisible(False)
        hbox.addWidget(self._sql_db_label)

        self._sql_db_btn = QPushButton("Choose DB…")
        self._sql_db_btn.setStyleSheet(
            "QPushButton{background:#313244;color:#f9e2af;border:1px solid #45475a;"
            "border-radius:4px;padding:2px 8px;font-size:11px;}"
            "QPushButton:hover{background:#45475a;}"
        )
        self._sql_db_btn.clicked.connect(self._select_sql_db)
        self._sql_db_btn.setVisible(False)
        hbox.addWidget(self._sql_db_btn)

        ref_btn = QPushButton("Reference")
        ref_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#7f849c;border:none;font-size:11px;padding:2px 8px;}"
            "QPushButton:hover{color:#cdd6f4;}"
        )
        ref_btn.clicked.connect(self._show_command_reference)
        hbox.addWidget(ref_btn)

        env_btn = QPushButton("Env Info")
        env_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#7f849c;border:none;font-size:11px;padding:2px 8px;}"
            "QPushButton:hover{color:#cdd6f4;}"
        )
        env_btn.clicked.connect(self._show_env_info)
        hbox.addWidget(env_btn)

        self._term_stop_btn = QPushButton("■ Stop")
        self._term_stop_btn.setStyleSheet(
            "QPushButton{background:#d20f39;color:white;border:none;border-radius:4px;"
            "padding:2px 10px;font-size:11px;font-weight:bold;}"
            "QPushButton:hover{background:#e81a44;}"
            "QPushButton:disabled{background:#313244;color:#585b70;}"
        )
        self._term_stop_btn.setEnabled(False)
        self._term_stop_btn.clicked.connect(self._term_stop)
        hbox.addWidget(self._term_stop_btn)

        close_btn = QPushButton("✕")
        close_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#6c7086;border:none;font-size:13px;padding:0 4px;}"
            "QPushButton:hover{color:#cdd6f4;}"
        )
        close_btn.clicked.connect(lambda: self._terminal_panel_widget.setVisible(False))
        hbox.addWidget(close_btn)

        tlay.addWidget(hdr)

        # Terminal output area
        self._term_output = QPlainTextEdit()
        self._term_output.setReadOnly(True)
        self._term_output.setStyleSheet(
            "QPlainTextEdit{background:#11111b;color:#cdd6f4;border:none;padding:8px;"
            "font-family:'JetBrains Mono','Fira Code','Consolas','Courier New',monospace;"
            "font-size:12px;}"
        )
        self._term_output.document().setMaximumBlockCount(3000)
        tlay.addWidget(self._term_output)

        # Input row
        input_row = QWidget()
        input_row.setStyleSheet("background:#181825; border-top:1px solid #313244;")
        ilay = QHBoxLayout(input_row)
        ilay.setContentsMargins(8, 4, 8, 4)
        ilay.setSpacing(6)

        prompt = QLabel("$")
        prompt.setStyleSheet("color:#a6e3a1; font-weight:bold; font-size:13px; font-family:monospace;")
        ilay.addWidget(prompt)

        self._term_input = QLineEdit()
        self._term_input.setPlaceholderText("Enter command and press Enter…")
        self._term_input.setStyleSheet(
            "QLineEdit{background:#1e1e2e;color:#a6e3a1;border:1px solid #45475a;"
            "border-radius:4px;padding:4px 8px;"
            "font-family:'JetBrains Mono','Fira Code','Consolas','Courier New',monospace;"
            "font-size:12px;}"
            "QLineEdit:focus{border:1px solid #89b4fa;}"
        )
        self._term_input.returnPressed.connect(self._term_execute)
        self._term_input.installEventFilter(self)
        ilay.addWidget(self._term_input)

        run_cmd_btn = QPushButton("Run ↵")
        run_cmd_btn.setStyleSheet(
            "QPushButton{background:#313244;color:#cdd6f4;border:none;border-radius:4px;"
            "padding:4px 12px;font-size:11px;font-weight:bold;}"
            "QPushButton:hover{background:#45475a;}"
        )
        run_cmd_btn.clicked.connect(self._term_execute)
        ilay.addWidget(run_cmd_btn)

        tlay.addWidget(input_row)

        # Add terminal panel to main vertical splitter
        self._v_splitter.addWidget(self._terminal_panel_widget)
        self._v_splitter.setSizes([440, 180, 150])
        self._terminal_dock = self._terminal_panel_widget  # reference

        # Connect tab change to update SQL DB selector visibility
        self._tab_widget.currentChanged.connect(self._on_tab_changed_terminal)

        # Greet
        host = get_host_os_name()
        self._term_append(
            f"Nitin Editor Terminal  |  Host OS: {host}\n"
            f"Linux: real execution  |  macOS/Windows: compatibility info only\n"
            f"Type 'help' for quick reference. Type 'clear' to clear output.\n\n",
            "#89b4fa",
        )

    def eventFilter(self, obj, event) -> bool:
        """Handle universal shortcuts (Zoom In/Out/Reset) and terminal input navigation."""
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QKeyEvent as QKE

        if event.type() == QEvent.Type.KeyPress:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Zoom In: Ctrl++ or Ctrl+=
                if (
                    event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal)
                    or event.text() in ("+", "=")
                ):
                    self._zoom_in()
                    return True
                # Zoom Out: Ctrl+- or Ctrl+_ or Ctrl+hyphen
                elif (
                    event.key() in (Qt.Key.Key_Minus, Qt.Key.Key_Underscore, Qt.Key.Key_hyphen)
                    or event.text() in ("-", "_", "", "–", "—")
                ):
                    self._zoom_out()
                    return True
                # Zoom Reset: Ctrl+0
                elif event.key() == Qt.Key.Key_0 or event.text() == "0":
                    self._zoom_reset()
                    return True
        if hasattr(self, "_term_input") and obj is self._term_input:
            if event.type() == QEvent.Type.KeyPress:
                key = event.key()
                if key == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    if self._runner_thread and self._runner_thread.isRunning():
                        self._term_append("^C\n", "#f9e2af")
                        self._stop_execution()
                        return True
                if key == Qt.Key.Key_Up:
                    self._term_history_up()
                    return True
                elif key == Qt.Key.Key_Down:
                    self._term_history_down()
                    return True
        return super().eventFilter(obj, event)

    def _term_history_up(self) -> None:
        if not self._term_history:
            return
        self._term_history_pos = min(
            self._term_history_pos + 1, len(self._term_history) - 1
        )
        self._term_input.setText(self._term_history[self._term_history_pos])

    def _term_history_down(self) -> None:
        if self._term_history_pos <= 0:
            self._term_history_pos = -1
            self._term_input.clear()
            return
        self._term_history_pos -= 1
        self._term_input.setText(self._term_history[self._term_history_pos])

    def _on_tab_changed_terminal(self, _idx: int) -> None:
        """Show/hide SQL DB selector when current tab language is SQL."""
        state = self._current_state()
        is_sql = state is not None and state.language == "SQL"
        if hasattr(self, "_sql_db_label"):
            self._sql_db_label.setVisible(is_sql)
        if hasattr(self, "_sql_db_btn"):
            self._sql_db_btn.setVisible(is_sql)

    def _term_execute(self) -> None:
        """Send live program input, or execute a shell command when idle."""
        raw = self._term_input.text()
        self._on_terminal_input_submitted(raw)

    def _on_terminal_input_submitted(self, raw: str) -> None:
        self._term_history_pos = -1

        if self._runner_thread and self._runner_thread.isRunning():
            sent = self._runner_thread.send_stdin(raw + "\n")
            if not sent:
                self._term_append("[process stdin is closed]\n", "#f9e2af")
            return

        cmd = raw.strip()

        if not cmd:
            return

        # Built-in commands
        if cmd == "clear":
            if hasattr(self, "_term_console"):
                self._term_console.clear_terminal()
            elif hasattr(self, "_term_output"):
                self._term_output.clear()
            return
        if cmd in ("help", "?"):
            self._term_append(get_reference_text() + "\n\n", "#89b4fa")
            return

        # Add to persistent history
        self._term_history = history_add(self._term_history, cmd)
        save_history(self._term_history)
        if hasattr(self, "_term_console"):
            self._term_console.set_history(self._term_history)

        target_os = self._term_os_combo.currentText() if hasattr(self, "_term_os_combo") else "Linux"

        # Safety check (only for Linux commands that will actually execute)
        if target_os == "Linux" and self._settings.get("terminal_confirm_dangerous", True):
            danger = check_command(cmd, target_os)
            if danger.is_dangerous:
                msg = warning_message(cmd, danger.reason)
                reply = QMessageBox.warning(
                    self,
                    "Dangerous Command",
                    msg,
                    QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok,
                    QMessageBox.StandardButton.Cancel,
                )
                if reply != QMessageBox.StandardButton.Ok:
                    self._term_append("  [Command cancelled by user]\n\n", "#f9e2af")
                    return

        # Run in background thread
        if self._term_running:
            self._term_append("⚠  Another command is already running.\n\n", "#f9e2af")
            return

        timeout = self._settings.get("terminal_timeout", 30)
        self._term_thread = _TermThread(cmd, target_os, timeout, str(Path.home()), parent=self)
        self._term_thread.stdout_sig.connect(
            lambda t: self._term_append(t, "#cdd6f4")
        )
        self._term_thread.stderr_sig.connect(
            lambda t: self._term_append(t, "#f38ba8")
        )
        self._term_thread.done_sig.connect(self._on_term_finished)
        self._term_running = True
        if hasattr(self, "_term_stop_btn"):
            self._term_stop_btn.setEnabled(True)
        self._term_thread.start()

    def _on_term_finished(self, result: CommandResult) -> None:
        self._term_running = False
        if hasattr(self, "_term_stop_btn"):
            self._term_stop_btn.setEnabled(False)

        if result.simulated:
            pass  # Message already emitted via on_stdout callback
        elif result.timed_out:
            self._term_append("\n⏱  Command timed out.\n\n", "#f9e2af")
        elif result.cancelled:
            self._term_append("\n⏹  Stopped.\n\n", "#f9e2af")
        elif result.error_message:
            self._term_append(f"\n❌  {result.error_message}\n\n", "#f38ba8")
        else:
            exit_str = f"(exit {result.exit_code})" if result.exit_code != 0 else ""
            self._term_append(f"\n{exit_str}\n" if exit_str else "\n", "#6c7086")

    def _term_stop(self) -> None:
        if hasattr(self, "_term_thread") and self._term_thread.isRunning():
            self._term_thread.stop()

    def _term_append(self, text: str, color: str = "#cdd6f4") -> None:
        if hasattr(self, "_term_console"):
            self._term_console._append_chunk(text, color)
        elif hasattr(self, "_term_output") and hasattr(self._term_output, "_append_chunk"):
            self._term_output._append_chunk(text, color)
        elif hasattr(self, "_term_output"):
            cursor = self._term_output.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            fmt = cursor.charFormat()
            fmt.setForeground(QColor(color))
            cursor.setCharFormat(fmt)
            cursor.insertText(text)
            self._term_output.setTextCursor(cursor)
            self._term_output.ensureCursorVisible()


    # ── Command reference / environment ──────────────────────────────────────

    def _show_command_reference(self) -> None:
        """Show the cross-platform command reference in a dialog."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Cross-Platform Command Reference")
        ref = get_reference_text()
        msg.setText(f"<pre style='font-size:11px;'>{ref}</pre>")
        msg.setStyleSheet(DARK_STYLE)
        msg.exec()

    def _show_env_info(self) -> None:
        """Show real environment information for the current host OS."""
        import shutil

        lines: list[str] = []

        def _ver(cmd: str) -> str:
            try:
                r = __import__("subprocess").run(
                    cmd.split(), capture_output=True, text=True, timeout=3
                )
                return (r.stdout or r.stderr).strip().split("\n")[0]
            except Exception:
                return ""

        host_os = get_host_os_name()
        uname = os.uname() if hasattr(os, "uname") else None
        lines.append(f"Host OS:      {host_os}")
        lines.append(f"Platform:     {sys.platform}")
        lines.append(f"Architecture: {uname.machine if uname else 'unknown'}")
        lines.append(f"Kernel:       {uname.release if uname else 'unknown'}")
        lines.append(f"Python:       {sys.version.split()[0]} ({shutil.which('python3') or 'not found'})")
        lines.append("")

        tools = [
            ("node", "Node.js"),
            ("gcc", "GCC"),
            ("g++", "G++"),
            ("java", "Java"),
            ("sqlite3", "SQLite CLI"),
            ("git", "Git"),
            ("bash", "Bash"),
        ]
        for cmd, label in tools:
            path = shutil.which(cmd)
            if path:
                ver = _ver(f"{cmd} --version")
                lines.append(f"{label:<14}{ver or path}")
            else:
                lines.append(f"{label:<14}not found")

        text = "\n".join(lines)
        msg = QMessageBox(self)
        msg.setWindowTitle("Environment Information")
        msg.setText(f"<pre style='font-size:12px;'>{text}</pre>")
        msg.setStyleSheet(DARK_STYLE)
        msg.exec()

    # ── Help dialogs ──────────────────────────────────────────────────────────

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Nitin Editor",
            "<h2>Nitin Editor</h2>"
            "<p>A private local coding IDE for Nitin.</p>"
            "<p><b>Version:</b> 1.2.0<br>"
            "<b>Platform:</b> Ubuntu Linux / GNOME (Wayland)<br>"
            "<b>Built with:</b> Python 3 · PySide6 6.x</p>"
            "<p>Runs completely locally.<br>"
            "No cloud. No telemetry. No accounts.</p>"
            "<p><b>Supported Languages:</b><br>"
            "Python · C · C++ · Java · JavaScript · HTML · CSS · SQL</p>"
            "<p><b>Terminal:</b><br>"
            "Linux (real execution) · macOS / Windows (compatibility info)</p>",
        )

    def _show_shortcuts(self) -> None:
        txt = """<h3>Keyboard Shortcuts</h3><table cellspacing="4">
<tr><td><b>Ctrl+Enter</b></td><td>Run code</td></tr>
<tr><td><b>F5</b></td><td>Run code</td></tr>
<tr><td><b>Ctrl+Shift+C</b></td><td>Stop execution</td></tr>
<tr><td><b>Ctrl+N</b></td><td>New tab</td></tr>
<tr><td><b>Ctrl+T</b></td><td>New tab</td></tr>
<tr><td><b>Ctrl+O</b></td><td>Open file</td></tr>
<tr><td><b>Ctrl+S</b></td><td>Save</td></tr>
<tr><td><b>Ctrl+Shift+S</b></td><td>Save As</td></tr>
<tr><td><b>Ctrl+W</b></td><td>Close tab</td></tr>
<tr><td><b>Ctrl+Z</b></td><td>Undo</td></tr>
<tr><td><b>Ctrl+Y</b></td><td>Redo</td></tr>
<tr><td><b>Ctrl+X / C / V</b></td><td>Cut / Copy / Paste</td></tr>
<tr><td><b>Ctrl+A</b></td><td>Select All</td></tr>
<tr><td><b>Ctrl+F</b></td><td>Find</td></tr>
<tr><td><b>Ctrl+H</b></td><td>Find &amp; Replace</td></tr>
<tr><td><b>Ctrl+Shift+P</b></td><td>HTML/CSS Preview</td></tr>
<tr><td><b>Ctrl++ / Ctrl+=</b></td><td>Zoom In</td></tr>
<tr><td><b>Ctrl+-</b></td><td>Zoom Out</td></tr>
<tr><td><b>Ctrl+0</b></td><td>Reset Zoom</td></tr>
<tr><td><b>Ctrl+Tab</b></td><td>Next Tab</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>Quit</td></tr>
</table>"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setText(txt)
        msg.setStyleSheet(DARK_STYLE)
        msg.exec()

    def _show_compiler_status(self) -> None:
        tools = [
            ("python3", "Python"),
            ("gcc",     "C"),
            ("g++",     "C++"),
            ("javac",   "Java compiler"),
            ("java",    "Java runtime"),
            ("node",    "JavaScript (Node.js)"),
        ]
        lines = []
        for cmd, label in tools:
            import shutil
            path = shutil.which(cmd)
            if path:
                lines.append(f"<tr><td>✅ {label}</td><td style='color:#7f849c'>{path}</td></tr>")
            else:
                lines.append(f"<tr><td>❌ {label}</td><td style='color:#f38ba8'>not found in PATH</td></tr>")
        html = f"<h3>Compiler / Runtime Status</h3><table cellspacing='4'>{''.join(lines)}</table>"
        msg = QMessageBox(self)
        msg.setWindowTitle("Compiler Status")
        msg.setText(html)
        msg.setStyleSheet(DARK_STYLE)
        msg.exec()

    # ── Window close ─────────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:  # type: ignore[override]
        unsaved = []
        for i in range(self._tab_widget.count()):
            container = self._tab_widget.widget(i)
            if container:
                state = self._tab_states.get(id(container))
                if state and state.is_modified:
                    unsaved.append(state.title)

        if unsaved:
            if os.environ.get("QT_QPA_PLATFORM") == "offscreen" or (
                QApplication.instance() and QApplication.instance().platformName() == "offscreen"
            ):
                reply = QMessageBox.StandardButton.Discard
            else:
                names = "\n  • ".join(unsaved)
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    f"Unsaved changes in:\n  • {names}\n\nDiscard and exit?",
                    QMessageBox.StandardButton.Discard
                    | QMessageBox.StandardButton.Save
                    | QMessageBox.StandardButton.Cancel,
                )
            if reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if reply == QMessageBox.StandardButton.Save:
                self._save_file()

        # Stop running process / thread
        if self._runner_thread:
            if self._runner_thread.isRunning():
                self._runner_thread.stop_execution()
                self._runner_thread.wait(3000)
            else:
                self._runner_thread.wait(500)

        # Stop SQL thread if exists
        if hasattr(self, "_sql_thread") and self._sql_thread:
            if self._sql_thread.isRunning():
                self._sql_thread.wait(1000)
            else:
                self._sql_thread.wait(500)

        # Stop terminal process/thread if exists
        if hasattr(self, "_term_thread") and self._term_thread:
            if self._term_thread.isRunning():
                self._term_thread.stop()
                self._term_thread.wait(2000)
            else:
                self._term_thread.wait(500)

        from PySide6.QtCore import QCoreApplication
        QCoreApplication.processEvents()

        # Persist terminal history
        save_history(self._term_history)

        save_settings(self._settings)
        event.accept()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="ncode",
        description="Nitin Editor — Local Code Playground",
    )
    parser.add_argument("file", nargs="?", help="Optional file to open")
    args, _ = parser.parse_known_args()

    # Platform detection: prefer Wayland when available, fall back to xcb
    import shutil as _shutil
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "")
    xdg_runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    wayland_socket = Path(xdg_runtime) / "wayland-0"

    if wayland_display and wayland_socket.exists():
        os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
    else:
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

    from PySide6.QtCore import QCoreApplication
    try:
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    except Exception:
        pass

    os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
    flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    if not flags:
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox --disable-dev-shm-usage"

    os.environ.setdefault("XDG_RUNTIME_DIR", xdg_runtime)

    app = QApplication(sys.argv)
    app.setApplicationName("Nitin Editor")
    app.setApplicationVersion("1.1.0")
    app.setOrganizationName("Nitin")
    app.setStyle("Fusion")

    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))

    initial_file: Path | None = None
    if args.file:
        p = Path(args.file).resolve()
        if p.exists():
            initial_file = p
        else:
            print(f"Warning: file not found: {p}", file=sys.stderr)

    window = NitinEditor(initial_file=initial_file)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
