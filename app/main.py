"""
Nitin Editor - main.py
Main application window and entry point.

Architecture:
  NitinEditor (QMainWindow)
    ├── QTabWidget  (editor tabs, each holding a CodeEditor)
    ├── Input Panel  (QPlainTextEdit — stdin for the running program)
    └── Output Panel (QPlainTextEdit — stdout/stderr display)
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

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import (
    QAction, QFont, QIcon, QKeySequence, QColor,
    QTextCursor, QTextDocument,
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QPlainTextEdit, QTextEdit, QLabel,
    QPushButton, QComboBox, QFileDialog, QMessageBox, QStatusBar,
    QToolBar, QMenu, QFrame, QDialog, QLineEdit, QCheckBox,
)

from app.compiler import (
    LANGUAGES, LANGUAGE_EXTENSIONS, detect_language,
    get_missing_tools, check_tool,
)
from app.runner import RunnerThread
from app.settings import load_settings, save_settings, load_recent_files, add_recent_file
from app.ui.settings_dialog import SettingsDialog

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
        '<!DOCTYPE html>\n<html>\n<head>\n'
        '    <title>Nitin Editor</title>\n</head>\n<body>\n'
        '    <h1>Hello, Nitin!</h1>\n    <p>Welcome to Nitin Editor.</p>\n'
        '</body>\n</html>\n'
    ),
    "CSS": (
        '/* CSS Preview */\nbody {\n    background: #1e1e2e;\n'
        '    color: #cdd6f4;\n    font-family: Arial, sans-serif;\n'
        '    padding: 20px;\n}\n\nh1 {\n    color: #89b4fa;\n}\n'
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

        self._setup_window()
        self._build_ui()
        self._apply_settings()
        self._new_tab()   # Start with one empty tab

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
        self._add_menu_action(view_menu, "Zoom &In",         self._zoom_in,          "Ctrl+=")
        self._add_menu_action(view_menu, "Zoom &Out",        self._zoom_out,         "Ctrl+-")
        self._add_menu_action(view_menu, "Reset &Zoom",      self._zoom_reset,       "Ctrl+0")

        # Run
        run_menu = mb.addMenu("&Run")
        run_menu.addAction(self._action_run)
        run_menu.addAction(self._action_stop)
        run_menu.addSeparator()
        self._add_menu_action(run_menu, "🌐  &Preview (HTML/CSS)", self._show_preview, "Ctrl+Shift+P")

        # Tabs
        tab_menu = mb.addMenu("&Tabs")
        tab_menu.addAction(self._action_new)
        tab_menu.addAction(self._action_close_tab)
        self._add_menu_action(tab_menu, "Next Tab",          self._next_tab,         "Ctrl+Tab")
        self._add_menu_action(tab_menu, "Previous Tab",      self._prev_tab,         "Ctrl+Shift+Tab")

        # Settings
        settings_menu = mb.addMenu("&Settings")
        self._add_menu_action(settings_menu, "⚙  Preferences…", self._show_settings)

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
        shortcut: str | None = None,
    ) -> QAction:
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
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

        tb.addSeparator()
        tb.addAction(tb_action("⚙", self._show_settings, tip="Preferences"))

    def _build_central(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._tab_widget = QTabWidget()
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.setMovable(True)
        self._tab_widget.tabCloseRequested.connect(self._close_tab)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

        self._v_splitter = QSplitter(Qt.Orientation.Vertical)
        self._v_splitter.addWidget(self._tab_widget)

        bottom = QWidget()
        bottom.setStyleSheet("background:#181825;")
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)

        self._h_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._h_splitter.addWidget(self._make_input_panel())
        self._h_splitter.addWidget(self._make_output_panel())
        self._h_splitter.setSizes([260, 740])

        bottom_layout.addWidget(self._h_splitter)
        self._v_splitter.addWidget(bottom)
        self._v_splitter.setSizes([520, 200])

        root.addWidget(self._v_splitter)

    def _make_input_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with Clear and EOF buttons
        hdr = QWidget()
        hdr.setFixedHeight(32)
        hdr.setStyleSheet("background:#1a1a2e; border-bottom: 1px solid #313244;")
        hbox = QHBoxLayout(hdr)
        hbox.setContentsMargins(10, 0, 6, 0)
        title = QLabel("⌨  CONSOLE / STDIN")
        title.setStyleSheet("color:#89b4fa; font-size:12px; font-weight:bold;")
        hbox.addWidget(title)
        hbox.addStretch()

        eof_btn = QPushButton("EOF (Ctrl+D)")
        eof_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#f9e2af;border:none;"
            "font-size:11px;padding:2px 8px;}"
            "QPushButton:hover{color:#ffffff;}"
        )
        eof_btn.clicked.connect(self._send_eof)
        hbox.addWidget(eof_btn)

        clear_in_btn = QPushButton("Clear")
        clear_in_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#6c7086;border:none;"
            "font-size:11px;padding:2px 8px;}"
            "QPushButton:hover{color:#cdd6f4;}"
        )
        clear_in_btn.clicked.connect(lambda: (self._input_area.clear(), self._live_input.clear()))
        hbox.addWidget(clear_in_btn)
        layout.addWidget(hdr)

        self._input_area = QPlainTextEdit()
        self._input_area.setPlaceholderText(
            "Console history & preloaded input (stdin)…\n\n"
            "Preload input here before clicking RUN,\n"
            "or type live input in the line below while running."
        )
        self._input_area.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {INPUT_BG};
                color: #cdd6f4;
                border: none;
                padding: 8px;
                font-family: "JetBrains Mono","Fira Code","Consolas","Courier New",monospace;
                font-size: 12px;
            }}
        """)
        layout.addWidget(self._input_area)

        # Bottom row for live interactive stdin entry
        bottom_row = QWidget()
        bottom_row.setStyleSheet("background:#181825; border-top: 1px solid #313244;")
        row_layout = QHBoxLayout(bottom_row)
        row_layout.setContentsMargins(6, 4, 6, 4)
        row_layout.setSpacing(6)

        prompt_lbl = QLabel(">")
        prompt_lbl.setStyleSheet("color:#a6e3a1; font-weight:bold; font-size:13px;")
        row_layout.addWidget(prompt_lbl)

        self._live_input = QLineEdit()
        self._live_input.setPlaceholderText("Type input and press Enter…")
        self._live_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e2e;
                color: #a6e3a1;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 4px 8px;
                font-family: "JetBrains Mono","Fira Code","Consolas","Courier New",monospace;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #89b4fa;
            }
        """)
        self._live_input.returnPressed.connect(self._send_live_input)
        row_layout.addWidget(self._live_input)

        self._send_btn = QPushButton("Send ↵")
        self._send_btn.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45475a;
                color: #ffffff;
            }
        """)
        self._send_btn.clicked.connect(self._send_live_input)
        row_layout.addWidget(self._send_btn)

        layout.addWidget(bottom_row)
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

        # Status bar at bottom of output panel
        self._exec_status = QLabel("")
        self._exec_status.setStyleSheet(
            "background:#181825; color:#7f849c; font-size:11px;"
            " padding: 3px 10px; border-top: 1px solid #313244;"
        )
        layout.addWidget(self._exec_status)
        return panel

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
        editor.textChanged.connect(
            lambda: self._on_editor_modified(id(container))
        )
        if hasattr(editor, "cursor_position_changed"):
            editor.cursor_position_changed.connect(self._update_cursor_status)
        elif hasattr(editor, "cursorPositionChanged"):
            editor.cursorPositionChanged.connect(
                lambda: self._update_cursor_from_editor(editor)
            )

        # Set language for syntax highlighting
        if hasattr(editor, "set_language"):
            editor.set_language(lang)

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
        ed.set_font_size = lambda s: ed.setFont(QFont("monospace", s))  # type: ignore[attr-defined]
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
        state = self._current_state()
        if state:
            state.language = language
        editor = self._current_editor()
        if editor and hasattr(editor, "set_language"):
            editor.set_language(language)
        self._update_language_ui(language)
        self._update_status_bar()

    def _update_language_ui(self, language: str) -> None:
        is_web = language in ("HTML", "CSS")
        self._preview_btn.setVisible(is_web)
        self._run_btn.setVisible(not is_web)

    # ── File operations ───────────────────────────────────────────────────────

    def _open_file(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            str(Path.home()),
            "All Supported (*.py *.c *.cpp *.cc *.cxx *.java *.js *.html *.htm *.css);;"
            "Python (*.py);;C (*.c);;C++ (*.cpp *.cc *.cxx);;Java (*.java);;"
            "JavaScript (*.js);;HTML (*.html *.htm);;CSS (*.css);;All Files (*)",
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
        self._settings["font_size"] = min(self._settings.get("font_size", 14) + 1, 40)
        self._apply_settings()

    def _zoom_out(self) -> None:
        self._settings["font_size"] = max(self._settings.get("font_size", 14) - 1, 6)
        self._apply_settings()

    def _zoom_reset(self) -> None:
        self._settings["font_size"] = 14
        self._apply_settings()

    # ── Run / Stop ────────────────────────────────────────────────────────────

    def _run_code(self) -> None:
        state = self._current_state()
        if state is None:
            return
        editor = self._current_editor()
        if editor is None:
            return

        # HTML/CSS → preview
        if state.language in ("HTML", "CSS"):
            self._show_preview()
            return

        code = editor.get_text().strip()
        if not code:
            self._clear_output()
            self._append_output("⚠  No code to run.\n", "#f9e2af")
            return

        # Check tools first
        missing = get_missing_tools(state.language)
        if missing:
            self._clear_output()
            self._append_output(
                f"❌  Missing tools: {', '.join(missing)}\n"
                f"    Install: sudo apt-get install {' '.join(missing)}\n",
                "#f38ba8",
            )
            return

        # Already running?
        if self._runner_thread and self._runner_thread.isRunning():
            return

        stdin_data = self._input_area.toPlainText()
        timeout = self._settings.get("execution_timeout", 10)

        self._clear_output()
        self._set_running_state(True)

        self._runner_thread = RunnerThread(self)
        self._runner_thread.configure(
            language=state.language,
            code=code,
            stdin_data=stdin_data,
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
        else:
            self._set_running_state(False)
            self._set_status("Ready")

    def _send_live_input(self) -> None:
        text = self._live_input.text()
        self._live_input.clear()

        if not text and not (self._runner_thread and self._runner_thread.isRunning()):
            return

        data_to_send = text + "\n"

        if self._runner_thread and self._runner_thread.isRunning():
            self._runner_thread.send_stdin(data_to_send)
            self._input_area.appendPlainText(f"> {text}")
            self._set_status(f"Sent stdin: {text}")
        else:
            self._input_area.appendPlainText(text)

    def _send_eof(self) -> None:
        if self._runner_thread and self._runner_thread.isRunning():
            self._runner_thread.close_stdin()
            self._input_area.appendPlainText("[EOF sent]")
            self._set_status("Sent EOF to process")

    def _set_running_state(self, running: bool) -> None:
        self._run_btn.setEnabled(not running)
        self._stop_btn.setEnabled(running)
        if running:
            self._set_status("Running…")
            self._exec_status.setText("  ⚡ Running…")
            self._exec_status.setStyleSheet(
                "background:#181825; color:#89b4fa; font-size:11px; padding:3px 10px; border-top:1px solid #313244;"
            )

    def _on_run_started(self) -> None:
        self._set_status("Running…")

    def _on_stdout_chunk(self, chunk: str) -> None:
        self._append_output(chunk, "#cdd6f4")

    def _on_stderr_chunk(self, chunk: str) -> None:
        self._append_output(chunk, "#f38ba8")

    def _on_runner_status(self, msg: str) -> None:
        self._set_status(msg)

    def _on_run_finished(self, result) -> None:
        # Always restore UI
        self._set_running_state(False)

        if result.error_message == "PREVIEW":
            self._show_preview()
            self._set_status("Preview rendered.")
            return

        if result.cancelled:
            self._append_output("\n⏹  Execution stopped by user.\n", "#f9e2af")
            self._set_status("Stopped.")
            self._exec_status.setText("  Stopped")
            self._exec_status.setStyleSheet(
                "background:#181825; color:#f9e2af; font-size:11px; padding:3px 10px; border-top:1px solid #313244;"
            )
            return

        if result.error_message:
            self._append_output(f"\n❌  {result.error_message}\n", "#f38ba8")
            self._set_status("Error.")
            self._exec_status.setText("  Error")
            self._exec_status.setStyleSheet(
                "background:#181825; color:#f38ba8; font-size:11px; padding:3px 10px; border-top:1px solid #313244;"
            )
            return

        # ── Compile errors ──
        if result.is_compile_error:
            self._clear_output()
            self._append_output("── COMPILE ERROR ──\n", "#fab387")
            if result.stderr:
                self._append_output(result.stderr, "#f38ba8")
            if result.stdout:
                self._append_output(result.stdout, "#f38ba8")

        if result.timed_out:
            self._append_output(
                f"\n⏱  Timed out after {self._settings.get('execution_timeout', 10)}s.\n",
                "#f9e2af",
            )

        # Status bar update
        if result.timed_out:
            status_text = "Timed out"
            status_color = "#f9e2af"
        elif result.is_compile_error:
            status_text = "Compile error"
            status_color = "#f38ba8"
        elif result.exit_code == 0:
            status_text = "Finished ✓"
            status_color = "#a6e3a1"
        else:
            status_text = f"Exit code: {result.exit_code}"
            status_color = "#f38ba8"

        self._set_status(status_text)
        self._exec_status.setText(
            f"  {status_text}   ·   Time: {result.elapsed_time:.3f}s   ·   Exit: {result.exit_code}"
        )
        self._exec_status.setStyleSheet(
            f"background:#181825; color:{status_color}; font-size:11px;"
            f" padding:3px 10px; border-top:1px solid #313244;"
        )

    # ── Output helpers ────────────────────────────────────────────────────────

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
        self._exec_status.setText("")
        self._exec_status.setStyleSheet(
            "background:#181825; color:#7f849c; font-size:11px;"
            " padding:3px 10px; border-top:1px solid #313244;"
        )

    # ── Preview ───────────────────────────────────────────────────────────────

    def _show_preview(self) -> None:
        state = self._current_state()
        editor = self._current_editor()
        if state is None or editor is None:
            return

        code = editor.get_text()

        if PreviewPanel is None or not HAS_WEBENGINE:
            QMessageBox.information(
                self,
                "Preview — No WebEngine",
                "HTML/CSS preview requires PySide6-WebEngine.\n\n"
                "Install with:\n"
                "  pip install PySide6-WebEngine\n\n"
                "Or your HTML file can be opened directly in a browser.",
            )
            return

        # Create / reuse dialog (never re-parent the panel)
        if self._preview_dialog is None or not self._preview_dialog.isVisible():
            self._preview_dialog = QDialog(self)
            self._preview_dialog.setWindowTitle("HTML/CSS Preview — Nitin Editor")
            self._preview_dialog.resize(900, 640)
            dlayout = QVBoxLayout(self._preview_dialog)
            dlayout.setContentsMargins(0, 0, 0, 0)
            if self._preview_panel is None:
                self._preview_panel = PreviewPanel()
            dlayout.addWidget(self._preview_panel)

        if state.language == "HTML":
            self._preview_panel.render_html(code)
        elif state.language == "CSS":
            self._preview_panel.render_css_only(code)

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
        self._status_ready.setText(text)

    # ── Help dialogs ──────────────────────────────────────────────────────────

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Nitin Editor",
            "<h2>Nitin Editor</h2>"
            "<p>A private local coding IDE for Nitin.</p>"
            "<p><b>Version:</b> 1.1.0<br>"
            "<b>Platform:</b> Ubuntu Linux / GNOME (Wayland)<br>"
            "<b>Built with:</b> Python 3 · PySide6 6.x</p>"
            "<p>Runs completely locally.<br>"
            "No cloud. No telemetry. No accounts.</p>"
            "<p><b>Supported Languages:</b><br>"
            "Python · C · C++ · Java · JavaScript · HTML · CSS</p>",
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
<tr><td><b>Ctrl+= / Ctrl+-</b></td><td>Zoom In / Out</td></tr>
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

        # Stop running process
        if self._runner_thread and self._runner_thread.isRunning():
            self._runner_thread.stop_execution()
            self._runner_thread.wait(3000)

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

    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox")
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
