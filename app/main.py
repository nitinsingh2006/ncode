"""
Nitin Editor - main.py
Main application window and entry point.
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# Ensure the project root is in sys.path when run directly
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize
from PySide6.QtGui import (
    QAction, QFont, QIcon, QKeySequence, QColor, QPalette,
    QTextCursor, QPixmap
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QPlainTextEdit, QTextEdit, QLabel,
    QPushButton, QComboBox, QFileDialog, QMessageBox, QStatusBar,
    QToolBar, QMenuBar, QMenu, QFrame, QSizePolicy, QTabBar,
    QDialog, QLineEdit, QCheckBox
)

from app.compiler import (
    LANGUAGES, LANGUAGE_EXTENSIONS, detect_language,
    get_missing_tools, check_tool
)
from app.runner import RunnerThread
from app.settings import load_settings, save_settings, load_recent_files, add_recent_file
from app.ui.settings_dialog import SettingsDialog

# Try to import preview
try:
    from app.preview import PreviewPanel, HAS_WEBENGINE
except ImportError:
    PreviewPanel = None  # type: ignore[assignment,misc]
    HAS_WEBENGINE = False

# ── Try to import editor ─────────────────────────────────────────────────────
try:
    from app.editor import make_editor, QSCI_BACKEND
except ImportError:
    make_editor = None  # type: ignore[assignment]
    QSCI_BACKEND = None

ASSETS_DIR = _ROOT / "assets"
ICON_PATH = ASSETS_DIR / "icon.png"

# ── Default code snippets per language ──────────────────────────────────────
DEFAULT_CODE: dict[str, str] = {
    "Python": '# Welcome to Nitin Editor\nprint("Hello, Nitin!")\n',
    "C": '#include <stdio.h>\n\nint main() {\n    printf("Hello, Nitin!\\n");\n    return 0;\n}\n',
    "C++": '#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "Hello, Nitin!" << endl;\n    return 0;\n}\n',
    "Java": 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, Nitin!");\n    }\n}\n',
    "JavaScript": '// Welcome to Nitin Editor\nconsole.log("Hello, Nitin!");\n',
    "HTML": '<!DOCTYPE html>\n<html>\n<head>\n    <title>Nitin Editor</title>\n</head>\n<body>\n    <h1>Hello, Nitin!</h1>\n    <p>Welcome to Nitin Editor.</p>\n</body>\n</html>\n',
    "CSS": '/* CSS Preview */\nbody {\n    background: #1e1e2e;\n    color: #cdd6f4;\n    font-family: Arial, sans-serif;\n    padding: 20px;\n}\n\nh1 {\n    color: #89b4fa;\n}\n',
}

# ── Style sheets ─────────────────────────────────────────────────────────────
DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", "Ubuntu", "Inter", Arial, sans-serif;
}
QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
    font-size: 13px;
    padding: 2px;
}
QMenuBar::item:selected { background-color: #313244; border-radius: 3px; }
QMenu {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 4px;
}
QMenu::item:selected { background-color: #313244; }
QMenu::separator { height: 1px; background: #313244; margin: 2px 8px; }
QToolBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    padding: 4px;
    spacing: 4px;
}
QTabWidget::pane {
    border: none;
    background-color: #1e1e2e;
}
QTabBar {
    background-color: #181825;
}
QTabBar::tab {
    background-color: #181825;
    color: #7f849c;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 6px 16px;
    font-size: 12px;
    min-width: 80px;
}
QTabBar::tab:selected {
    color: #cdd6f4;
    border-bottom: 2px solid #89b4fa;
    background-color: #1e1e2e;
}
QTabBar::tab:hover:!selected {
    color: #cdd6f4;
    background-color: #24273a;
}
QTabBar::close-button {
    image: none;
}
QSplitter::handle {
    background-color: #313244;
    width: 2px;
    height: 2px;
}
QPlainTextEdit, QTextEdit {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: none;
    selection-background-color: #313244;
    font-family: "JetBrains Mono", "Fira Code", "Consolas", "Courier New", monospace;
}
QScrollBar:vertical {
    background: #181825;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover { background: #6c7086; }
QScrollBar:horizontal {
    background: #181825;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #45475a;
    border-radius: 4px;
}
QScrollBar::add-line, QScrollBar::sub-line { background: none; }
QStatusBar {
    background-color: #181825;
    color: #7f849c;
    border-top: 1px solid #313244;
    font-size: 11px;
}
QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 100px;
}
QComboBox::drop-down { border: none; padding-right: 8px; }
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
    border: 1px solid #45475a;
}
QLineEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
}
QCheckBox { color: #cdd6f4; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    background: #313244;
    border: 1px solid #45475a;
    border-radius: 3px;
}
QCheckBox::indicator:checked {
    background: #89b4fa;
    border: 1px solid #89b4fa;
}
"""

LIGHT_STYLE = """
QMainWindow, QWidget {
    background-color: #f8f8f2;
    color: #282a36;
    font-family: "Segoe UI", "Ubuntu", "Inter", Arial, sans-serif;
}
QMenuBar { background-color: #e8e8e4; color: #282a36; border-bottom: 1px solid #ccc; }
QMenuBar::item:selected { background-color: #d8d8d4; }
QMenu { background-color: #f8f8f2; color: #282a36; border: 1px solid #ccc; }
QMenu::item:selected { background-color: #d8d8d4; }
QToolBar { background-color: #e8e8e4; border-bottom: 1px solid #ccc; padding: 4px; }
QTabBar::tab { background: #e8e8e4; color: #888; padding: 6px 16px; }
QTabBar::tab:selected { color: #282a36; border-bottom: 2px solid #6272a4; background: #f8f8f2; }
QPlainTextEdit, QTextEdit { background-color: #f8f8f2; color: #282a36; border: none; }
QStatusBar { background: #e8e8e4; color: #888; border-top: 1px solid #ccc; font-size: 11px; }
QComboBox { background: #e8e8e4; color: #282a36; border: 1px solid #ccc; border-radius: 4px; padding: 4px 8px; }
"""

BTN_RUN_STYLE = """
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #40a02b,stop:1 #2d7e1f);
    color: white;
    border: none;
    border-radius: 5px;
    padding: 6px 18px;
    font-size: 13px;
    font-weight: bold;
    min-width: 90px;
}
QPushButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #4ec135,stop:1 #36a024);
}
QPushButton:pressed { background: #2d7e1f; }
QPushButton:disabled { background: #313244; color: #6c7086; }
"""

BTN_STOP_STYLE = """
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #d20f39,stop:1 #a0102a);
    color: white;
    border: none;
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: bold;
    min-width: 80px;
}
QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #e81a44,stop:1 #b8153a); }
QPushButton:pressed { background: #a0102a; }
QPushButton:disabled { background: #313244; color: #6c7086; }
"""

BTN_PREVIEW_STYLE = """
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1e66f5,stop:1 #1353c5);
    color: white;
    border: none;
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: bold;
    min-width: 90px;
}
QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #2a78ff,stop:1 #1a64e0); }
QPushButton:pressed { background: #1353c5; }
QPushButton:disabled { background: #313244; color: #6c7086; }
"""

OUTPUT_BG = "#11111b"
OUTPUT_FG = "#cdd6f4"
INPUT_BG = "#181825"


# ── Tab document state ────────────────────────────────────────────────────────

class TabState:
    """Holds state for a single editor tab."""
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
        marker = "●  " if self.is_modified else ""
        return f"{marker}{self.title}"


# ── Find/Replace Dialog ──────────────────────────────────────────────────────

class FindReplaceDialog(QDialog):
    def __init__(self, editor_getter, parent=None):
        super().__init__(parent)
        self._get_editor = editor_getter
        self.setWindowTitle("Find & Replace")
        self.setModal(False)
        self.setMinimumWidth(380)
        self.setStyleSheet(DARK_STYLE)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # Find row
        find_row = QHBoxLayout()
        find_row.addWidget(QLabel("Find:"))
        self._find_input = QLineEdit()
        find_row.addWidget(self._find_input)
        layout.addLayout(find_row)

        # Replace row
        replace_row = QHBoxLayout()
        replace_row.addWidget(QLabel("Replace:"))
        self._replace_input = QLineEdit()
        replace_row.addWidget(self._replace_input)
        layout.addLayout(replace_row)

        # Options
        opts_row = QHBoxLayout()
        self._case_sensitive = QCheckBox("Case sensitive")
        opts_row.addWidget(self._case_sensitive)
        opts_row.addStretch()
        layout.addLayout(opts_row)

        # Buttons
        btn_row = QHBoxLayout()
        find_btn = QPushButton("Find Next")
        find_btn.clicked.connect(self._find_next)
        replace_btn = QPushButton("Replace")
        replace_btn.clicked.connect(self._replace)
        replace_all_btn = QPushButton("Replace All")
        replace_all_btn.clicked.connect(self._replace_all)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        for btn in (find_btn, replace_btn, replace_all_btn, close_btn):
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

    def _get_text(self) -> str:
        return self._find_input.text()

    def _find_next(self) -> None:
        query = self._get_text()
        if not query:
            return
        editor = self._get_editor()
        if hasattr(editor, "_editor"):  # QScintilla
            cs = self._case_sensitive.isChecked()
            editor._editor.findFirst(query, False, cs, False, True)
        elif hasattr(editor, "find"):
            flags = QTextDocument.FindFlag(0)
            if self._case_sensitive.isChecked():
                flags |= QTextDocument.FindFlag.FindCaseSensitively
            editor.find(query, flags)

    def _replace(self) -> None:
        query = self._get_text()
        replace = self._replace_input.text()
        editor = self._get_editor()
        if not query:
            return
        if hasattr(editor, "_editor"):  # QScintilla
            cs = self._case_sensitive.isChecked()
            if editor._editor.hasSelectedText():
                sel = editor._editor.selectedText()
                cmp = sel if cs else sel.lower()
                cmp_q = query if cs else query.lower()
                if cmp == cmp_q:
                    editor._editor.replaceSelectedText(replace)
            editor._editor.findFirst(query, False, cs, False, True)
        elif isinstance(editor, QPlainTextEdit):
            cursor = editor.textCursor()
            if cursor.hasSelection() and cursor.selectedText() == query:
                cursor.insertText(replace)
            editor.find(query)

    def _replace_all(self) -> None:
        query = self._get_text()
        replace = self._replace_input.text()
        editor = self._get_editor()
        if not query:
            return
        if hasattr(editor, "get_text") and hasattr(editor, "set_text"):
            text = editor.get_text()
            if self._case_sensitive.isChecked():
                new_text = text.replace(query, replace)
            else:
                import re
                new_text = re.sub(re.escape(query), replace, text, flags=re.IGNORECASE)
            editor.set_text(new_text)


# ── Main Window ───────────────────────────────────────────────────────────────

class NitinEditor(QMainWindow):
    def __init__(self, initial_file: Path | None = None) -> None:
        super().__init__()
        self._settings = load_settings()
        self._runner_thread: RunnerThread | None = None
        self._tab_states: dict[int, TabState] = {}  # widget_id → TabState
        self._find_dialog: FindReplaceDialog | None = None
        self._recent_files_actions: list[QAction] = []

        self._setup_window()
        self._build_ui()
        self._apply_settings()
        self._new_tab()

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

    def _build_ui(self) -> None:
        self._build_menu_bar()
        self._build_toolbar()
        self._build_central()
        self._build_status_bar()

    def _build_menu_bar(self) -> None:
        mb = self.menuBar()

        # File menu
        file_menu = mb.addMenu("&File")
        self._add_action(file_menu, "&New", self._new_tab, "Ctrl+N")
        self._add_action(file_menu, "&Open...", self._open_file, "Ctrl+O")
        file_menu.addSeparator()
        self._add_action(file_menu, "&Save", self._save_file, "Ctrl+S")
        self._add_action(file_menu, "Save &As...", self._save_file_as, "Ctrl+Shift+S")
        file_menu.addSeparator()
        self._recent_menu = file_menu.addMenu("Recent Files")
        self._refresh_recent_menu()
        file_menu.addSeparator()
        self._add_action(file_menu, "E&xit", self.close, "Ctrl+Q")

        # Edit menu
        edit_menu = mb.addMenu("&Edit")
        self._add_action(edit_menu, "&Undo", self._undo, "Ctrl+Z")
        self._add_action(edit_menu, "&Redo", self._redo, "Ctrl+Y")
        edit_menu.addSeparator()
        self._add_action(edit_menu, "Cu&t", self._cut, "Ctrl+X")
        self._add_action(edit_menu, "&Copy", self._copy, "Ctrl+C")
        self._add_action(edit_menu, "&Paste", self._paste, "Ctrl+V")
        self._add_action(edit_menu, "Select &All", self._select_all, "Ctrl+A")
        edit_menu.addSeparator()
        self._add_action(edit_menu, "&Find / Replace...", self._show_find_replace, "Ctrl+H")
        self._add_action(edit_menu, "Find...", self._show_find, "Ctrl+F")

        # View menu
        view_menu = mb.addMenu("&View")
        self._add_action(view_menu, "Zoom &In", self._zoom_in, "Ctrl+=")
        self._add_action(view_menu, "Zoom &Out", self._zoom_out, "Ctrl+-")
        self._add_action(view_menu, "Reset Zoom", self._zoom_reset, "Ctrl+0")

        # Run menu
        run_menu = mb.addMenu("&Run")
        self._add_action(run_menu, "▶  &Run", self._run_code, "Ctrl+Return")
        self._add_action(run_menu, "■  &Stop", self._stop_execution, "Ctrl+Shift+C")
        run_menu.addSeparator()
        self._add_action(run_menu, "🌐  &Preview (HTML/CSS)", self._show_preview, "Ctrl+Shift+P")

        # Tab menu
        tab_menu = mb.addMenu("&Tabs")
        self._add_action(tab_menu, "New Tab", self._new_tab, "Ctrl+T")
        self._add_action(tab_menu, "Close Tab", self._close_current_tab, "Ctrl+W")
        self._add_action(tab_menu, "Next Tab", self._next_tab, "Ctrl+Tab")
        self._add_action(tab_menu, "Previous Tab", self._prev_tab, "Ctrl+Shift+Tab")

        # Settings
        settings_menu = mb.addMenu("&Settings")
        self._add_action(settings_menu, "⚙  Preferences...", self._show_settings)

        # Help
        help_menu = mb.addMenu("&Help")
        self._add_action(help_menu, "&About Nitin Editor", self._show_about)
        self._add_action(help_menu, "Keyboard &Shortcuts", self._show_shortcuts)

    def _add_action(
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
        tb = QToolBar("Main Toolbar", self)
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        self.addToolBar(tb)

        # New / Open / Save
        tb.addAction(self._make_action("📄  New", self._new_tab, "Ctrl+N", "New file (Ctrl+N)"))
        tb.addAction(self._make_action("📂  Open", self._open_file, "Ctrl+O", "Open file (Ctrl+O)"))
        tb.addAction(self._make_action("💾  Save", self._save_file, "Ctrl+S", "Save file (Ctrl+S)"))
        tb.addSeparator()

        # Language selector
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

        # Run button
        self._run_btn = QPushButton("▶  RUN")
        self._run_btn.setStyleSheet(BTN_RUN_STYLE)
        self._run_btn.setToolTip("Run code (Ctrl+Enter)")
        self._run_btn.clicked.connect(self._run_code)
        tb.addWidget(self._run_btn)

        # Stop button
        self._stop_btn = QPushButton("■  STOP")
        self._stop_btn.setStyleSheet(BTN_STOP_STYLE)
        self._stop_btn.setToolTip("Stop execution (Ctrl+Shift+C)")
        self._stop_btn.clicked.connect(self._stop_execution)
        self._stop_btn.setEnabled(False)
        tb.addWidget(self._stop_btn)

        # Preview button (HTML/CSS)
        self._preview_btn = QPushButton("🌐  Preview")
        self._preview_btn.setStyleSheet(BTN_PREVIEW_STYLE)
        self._preview_btn.setToolTip("Preview HTML/CSS (Ctrl+Shift+P)")
        self._preview_btn.clicked.connect(self._show_preview)
        self._preview_btn.setVisible(False)
        tb.addWidget(self._preview_btn)

        tb.addSeparator()

        # Settings
        tb.addAction(self._make_action("⚙", self._show_settings, tooltip="Settings"))

    def _make_action(
        self, text: str, slot, shortcut: str | None = None, tooltip: str | None = None
    ) -> QAction:
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        if tooltip:
            action.setToolTip(tooltip)
        action.triggered.connect(slot)
        return action

    def _build_central(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Tabs widget
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.setMovable(True)
        self._tab_widget.tabCloseRequested.connect(self._close_tab)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

        # Vertical splitter: tabs + bottom panels
        self._v_splitter = QSplitter(Qt.Orientation.Vertical)
        self._v_splitter.addWidget(self._tab_widget)

        # Bottom area: input + output
        bottom = QWidget()
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(2)

        self._h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Input panel
        input_panel = self._make_input_panel()
        # Output panel
        output_panel = self._make_output_panel()

        self._h_splitter.addWidget(input_panel)
        self._h_splitter.addWidget(output_panel)
        self._h_splitter.setSizes([300, 700])

        bottom_layout.addWidget(self._h_splitter)

        self._v_splitter.addWidget(bottom)
        self._v_splitter.setSizes([500, 200])

        main_layout.addWidget(self._v_splitter)

        # Preview panel (initially hidden)
        if PreviewPanel is not None:
            self._preview_panel = PreviewPanel()
        else:
            self._preview_panel = None
        self._preview_visible = False

    def _make_input_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background:{INPUT_BG};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = self._panel_header("⌨  INPUT", "#313244")
        layout.addWidget(header)

        self._input_area = QPlainTextEdit()
        self._input_area.setPlaceholderText("Enter program input (stdin) here…")
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
        return panel

    def _make_output_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background:{OUTPUT_BG};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Output header with clear button
        hdr_widget = QWidget()
        hdr_widget.setFixedHeight(32)
        hdr_widget.setStyleSheet("background:#1a1a2e; border-bottom: 1px solid #313244;")
        hdr_h = QHBoxLayout(hdr_widget)
        hdr_h.setContentsMargins(10, 0, 8, 0)
        title = QLabel("📤  OUTPUT")
        title.setStyleSheet("color:#89b4fa; font-size:12px; font-weight:bold;")
        hdr_h.addWidget(title)
        hdr_h.addStretch()
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #6c7086;
                border: none; font-size: 11px; padding: 2px 8px;
            }
            QPushButton:hover { color: #cdd6f4; }
        """)
        clear_btn.clicked.connect(self._clear_output)
        hdr_h.addWidget(clear_btn)
        layout.addWidget(hdr_widget)

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
        layout.addWidget(self._output_area)

        # Status bar in output panel
        self._exec_status = QLabel("")
        self._exec_status.setStyleSheet(
            "background:#181825; color:#7f849c; font-size:11px;"
            " padding: 3px 10px; border-top: 1px solid #313244;"
        )
        layout.addWidget(self._exec_status)
        return panel

    def _panel_header(self, text: str, bg: str) -> QWidget:
        hdr = QWidget()
        hdr.setFixedHeight(32)
        hdr.setStyleSheet(f"background:{bg}; border-bottom: 1px solid #313244;")
        hbox = QHBoxLayout(hdr)
        hbox.setContentsMargins(10, 0, 8, 0)
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#89b4fa; font-size:12px; font-weight:bold;")
        hbox.addWidget(lbl)
        hbox.addStretch()
        return hdr

    def _build_status_bar(self) -> None:
        sb = QStatusBar()
        sb.setStyleSheet(
            "QStatusBar { background: #181825; color:#7f849c; font-size:11px; }"
        )
        self.setStatusBar(sb)

        self._status_lang = QLabel("Language: Python")
        self._status_cursor = QLabel("Ln 1, Col 1")
        self._status_spaces = QLabel("Spaces: 4")
        self._status_encoding = QLabel("UTF-8")
        self._status_ready = QLabel("Ready")
        self._status_ready.setStyleSheet("color:#a6e3a1; font-weight:bold;")

        for w in (
            self._status_lang, self._status_cursor, self._status_spaces,
            self._status_encoding, self._status_ready
        ):
            sb.addPermanentWidget(w)
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.VLine)
            sep.setStyleSheet("color:#313244;")
            sb.addPermanentWidget(sep)

    # ── Tab management ────────────────────────────────────────────────────────

    def _new_tab(
        self,
        title: str = "Untitled",
        language: str | None = None,
        file_path: Path | None = None,
        code: str | None = None,
    ) -> int:
        lang = language or self._lang_combo.currentText()
        state = TabState(title=title, language=lang, file_path=file_path)

        # Container widget for this tab
        container = QWidget()
        container.setStyleSheet("background:#1e1e2e;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        editor = make_editor(container) if make_editor else self._fallback_editor(container)
        layout.addWidget(editor)

        # Set initial code
        initial = code if code is not None else DEFAULT_CODE.get(lang, "")
        editor.set_text(initial)

        # Connect signals
        if hasattr(editor, "run_requested"):
            editor.run_requested.connect(self._run_code)
        if hasattr(editor, "text_changed"):
            editor.text_changed.connect(
                lambda: self._on_editor_modified(container)
            )
        elif hasattr(editor, "textChanged"):
            editor.textChanged.connect(
                lambda: self._on_editor_modified(container)
            )
        if hasattr(editor, "cursor_position_changed"):
            editor.cursor_position_changed.connect(self._update_cursor_status)
        elif hasattr(editor, "cursorPositionChanged"):
            editor.cursorPositionChanged.connect(
                lambda: self._update_cursor_from_editor(editor)
            )

        # Store in lookup
        cid = id(container)
        self._tab_states[cid] = state
        # Store editor reference in container
        container._editor_widget = editor  # type: ignore[attr-defined]

        idx = self._tab_widget.addTab(container, state.display_title)
        self._tab_widget.setCurrentIndex(idx)
        return idx

    def _fallback_editor(self, parent: QWidget) -> QPlainTextEdit:
        """Minimal QPlainTextEdit if make_editor is unavailable."""
        ed = QPlainTextEdit(parent)
        ed.setStyleSheet(
            "background:#1e1e2e; color:#cdd6f4; border:none;"
            " font-family:monospace; font-size:14px;"
        )
        ed.get_text = ed.toPlainText  # type: ignore[attr-defined]
        ed.set_text = ed.setPlainText  # type: ignore[attr-defined]
        ed.set_language = lambda _: None  # type: ignore[attr-defined]
        ed.set_font_size = lambda s: ed.setFont(QFont("monospace", s))  # type: ignore[attr-defined]
        ed.set_tab_size = lambda _: None  # type: ignore[attr-defined]
        ed.set_word_wrap = lambda _: None  # type: ignore[attr-defined]
        ed.get_cursor_position = lambda: (1, 1)  # type: ignore[attr-defined]
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
                f'"{state.title}" has unsaved changes.\nClose anyway?',
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
        if cid in self._tab_states:
            del self._tab_states[cid]
        self._tab_widget.removeTab(index)
        if self._tab_widget.count() == 0:
            self._new_tab()

    def _close_current_tab(self) -> None:
        idx = self._tab_widget.currentIndex()
        if idx >= 0:
            self._close_tab(idx)

    def _next_tab(self) -> None:
        idx = (self._tab_widget.currentIndex() + 1) % self._tab_widget.count()
        self._tab_widget.setCurrentIndex(idx)

    def _prev_tab(self) -> None:
        idx = (self._tab_widget.currentIndex() - 1) % self._tab_widget.count()
        self._tab_widget.setCurrentIndex(idx)

    def _on_tab_changed(self, index: int) -> None:
        state = self._current_state()
        if state:
            self._lang_combo.blockSignals(True)
            self._lang_combo.setCurrentText(state.language)
            self._lang_combo.blockSignals(False)
            self._update_language_ui(state.language)
            self._update_status_bar()

    def _on_editor_modified(self, container: QWidget) -> None:
        cid = id(container)
        state = self._tab_states.get(cid)
        if state and not state.is_modified:
            state.is_modified = True
            idx = self._tab_widget.indexOf(container)
            if idx >= 0:
                self._tab_widget.setTabText(idx, state.display_title)

    # ── Language management ───────────────────────────────────────────────────

    def _on_language_changed(self, language: str) -> None:
        state = self._current_state()
        if state:
            state.language = language
        editor = self._current_editor()
        if editor:
            editor.set_language(language)
        self._update_language_ui(language)
        self._update_status_bar()

    def _update_language_ui(self, language: str) -> None:
        is_web = language in ("HTML", "CSS")
        self._preview_btn.setVisible(is_web)
        self._run_btn.setVisible(language not in ("HTML", "CSS"))

    # ── File operations ───────────────────────────────────────────────────────

    def _new_tab_action(self) -> None:
        self._new_tab()

    def _open_file(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            str(Path.home()),
            "All Supported Files (*.py *.c *.cpp *.cc *.cxx *.java *.js *.html *.htm *.css);;"
            "Python (*.py);;C (*.c);;C++ (*.cpp *.cc *.cxx);;Java (*.java);;"
            "JavaScript (*.js);;HTML (*.html *.htm);;CSS (*.css);;All Files (*)",
        )
        if path_str:
            self._open_file_path(Path(path_str))

    def _open_file_path(self, path: Path) -> None:
        try:
            code = path.read_text(encoding="utf-8")
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not open file:\n{e}")
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
        default_name = state.title if state else f"Untitled{ext}"
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
            path.write_text(code, encoding="utf-8")
        except OSError as e:
            QMessageBox.critical(self, "Save Error", f"Could not save file:\n{e}")
            return False
        state = self._current_state()
        if state:
            state.is_modified = False
            idx = self._tab_widget.currentIndex()
            self._tab_widget.setTabText(idx, state.display_title)
        self._set_status("Saved: " + str(path))
        return True

    def _refresh_recent_menu(self) -> None:
        self._recent_menu.clear()
        files = load_recent_files()
        if not files:
            no_recent = QAction("(No recent files)", self)
            no_recent.setEnabled(False)
            self._recent_menu.addAction(no_recent)
            return
        for fp in files[:15]:
            action = QAction(fp, self)
            action.triggered.connect(lambda checked, p=fp: self._open_file_path(Path(p)))
            self._recent_menu.addAction(action)

    # ── Edit operations ───────────────────────────────────────────────────────

    def _undo(self) -> None:
        e = self._current_editor()
        if e:
            if hasattr(e, "_editor"):
                e._editor.undo()
            elif hasattr(e, "undo"):
                e.undo()

    def _redo(self) -> None:
        e = self._current_editor()
        if e:
            if hasattr(e, "_editor"):
                e._editor.redo()
            elif hasattr(e, "redo"):
                e.redo()

    def _cut(self) -> None:
        e = self._current_editor()
        if e:
            if hasattr(e, "_editor"):
                e._editor.cut()
            elif hasattr(e, "cut"):
                e.cut()

    def _copy(self) -> None:
        e = self._current_editor()
        if e:
            if hasattr(e, "_editor"):
                e._editor.copy()
            elif hasattr(e, "copy"):
                e.copy()

    def _paste(self) -> None:
        e = self._current_editor()
        if e:
            if hasattr(e, "_editor"):
                e._editor.paste()
            elif hasattr(e, "paste"):
                e.paste()

    def _select_all(self) -> None:
        e = self._current_editor()
        if e:
            if hasattr(e, "_editor"):
                e._editor.selectAll()
            elif hasattr(e, "selectAll"):
                e.selectAll()

    def _show_find(self) -> None:
        self._show_find_replace()

    def _show_find_replace(self) -> None:
        if self._find_dialog is None:
            self._find_dialog = FindReplaceDialog(self._current_editor, self)
        self._find_dialog.show()
        self._find_dialog.raise_()
        self._find_dialog.activateWindow()

    # ── Zoom ─────────────────────────────────────────────────────────────────

    def _zoom_in(self) -> None:
        self._settings["font_size"] = min(self._settings.get("font_size", 14) + 1, 32)
        self._apply_settings()

    def _zoom_out(self) -> None:
        self._settings["font_size"] = max(self._settings.get("font_size", 14) - 1, 8)
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

        # HTML/CSS → show preview instead
        if state.language in ("HTML", "CSS"):
            self._show_preview()
            return

        code = editor.get_text().strip()
        if not code:
            self._append_output("⚠  No code to run.\n", color="#f9e2af")
            return

        # Check tools
        missing = get_missing_tools(state.language)
        if missing:
            self._append_output(
                f"❌  Missing tools: {', '.join(missing)}\n"
                f"    Install with: sudo apt-get install {' '.join(missing)}\n",
                color="#f38ba8",
            )
            return

        stdin_data = self._input_area.toPlainText()
        timeout = self._settings.get("execution_timeout", 10)

        self._clear_output()
        self._set_status("Running…")
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)

        # Launch background thread
        self._runner_thread = RunnerThread(self)
        self._runner_thread.configure(
            language=state.language,
            code=code,
            stdin_data=stdin_data,
            timeout=timeout,
            saved_path=state.file_path,
        )
        self._runner_thread.started_signal.connect(self._on_run_started)
        self._runner_thread.finished_signal.connect(self._on_run_finished)
        self._runner_thread.start()

    def _stop_execution(self) -> None:
        if self._runner_thread and self._runner_thread.isRunning():
            self._runner_thread.stop_execution()
            self._append_output("\n⏹  Execution stopped by user.\n", color="#f9e2af")
            self._set_status("Stopped.")
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def _on_run_started(self) -> None:
        self._append_output("⏳  Running…\n", color="#7f849c")

    def _on_run_finished(self, result) -> None:
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

        if result.error_message == "PREVIEW":
            self._show_preview()
            self._set_status("Preview rendered.")
            return

        if result.error_message:
            self._append_output(f"❌  {result.error_message}\n", color="#f38ba8")
            self._set_status("Error.")
            return

        # Clear the "Running…" line
        self._output_area.clear()

        if result.stdout:
            self._append_output(result.stdout, color="#cdd6f4")

        if result.stderr:
            self._append_output("\n— STDERR —\n", color="#fab387")
            self._append_output(result.stderr, color="#f38ba8")

        if result.timed_out:
            self._append_output(
                f"\n⏱  Execution timed out after "
                f"{self._settings.get('execution_timeout', 10)}s.\n",
                color="#f9e2af",
            )
        elif result.cancelled:
            self._append_output("\n⏹  Cancelled.\n", color="#f9e2af")

        exit_color = "#a6e3a1" if result.exit_code == 0 else "#f38ba8"
        self._exec_status.setText(
            f"  Exit code: {result.exit_code}   ·   "
            f"Time: {result.elapsed_time:.3f}s"
        )
        self._exec_status.setStyleSheet(
            f"background:#181825; color:{exit_color}; font-size:11px;"
            f" padding: 3px 10px; border-top: 1px solid #313244;"
        )

        status_text = "Finished" if result.exit_code == 0 else f"Exit code: {result.exit_code}"
        self._set_status(status_text)

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

    # ── Preview ───────────────────────────────────────────────────────────────

    def _show_preview(self) -> None:
        state = self._current_state()
        editor = self._current_editor()
        if state is None or editor is None:
            return

        code = editor.get_text()

        if self._preview_panel is None:
            QMessageBox.warning(
                self, "Preview Unavailable",
                "HTML preview requires PySide6-WebEngine.\n"
                "Install with: pip install PySide6-WebEngine"
            )
            return

        if state.language == "HTML":
            self._preview_panel.render_html(code)
        elif state.language == "CSS":
            self._preview_panel.render_css_only(code)

        # Show in a separate dialog
        if not self._preview_visible:
            dialog = QDialog(self)
            dialog.setWindowTitle("HTML/CSS Preview — Nitin Editor")
            dialog.resize(900, 600)
            dlayout = QVBoxLayout(dialog)
            dlayout.setContentsMargins(0, 0, 0, 0)
            dlayout.addWidget(self._preview_panel)
            dialog.exec()

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
        self.setStyleSheet(DARK_STYLE if theme == "dark" else LIGHT_STYLE)

        font_size = self._settings.get("font_size", 14)
        tab_size = self._settings.get("tab_size", 4)
        word_wrap = self._settings.get("word_wrap", False)

        # Apply to all tabs
        for i in range(self._tab_widget.count()):
            container = self._tab_widget.widget(i)
            if container:
                editor = getattr(container, "_editor_widget", None)
                if editor:
                    if hasattr(editor, "set_font_size"):
                        editor.set_font_size(font_size)
                    if hasattr(editor, "set_tab_size"):
                        editor.set_tab_size(tab_size)
                    if hasattr(editor, "set_word_wrap"):
                        editor.set_word_wrap(word_wrap)

        self._status_spaces.setText(f"Spaces: {tab_size}")
        self._update_status_bar()

    # ── Status bar ────────────────────────────────────────────────────────────

    def _update_status_bar(self) -> None:
        state = self._current_state()
        if state:
            self._status_lang.setText(f"Language: {state.language}")

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
            "<p>A private local coding playground for Nitin.</p>"
            "<p><b>Version:</b> 1.0.0<br>"
            "<b>Platform:</b> Ubuntu Linux / GNOME<br>"
            "<b>Built with:</b> Python · PySide6 · QScintilla</p>"
            "<p>Runs completely locally. No cloud. No telemetry. No accounts.</p>",
        )

    def _show_shortcuts(self) -> None:
        shortcuts = """<h3>Keyboard Shortcuts</h3>
<table>
<tr><td><b>Ctrl+Enter</b></td><td>Run code</td></tr>
<tr><td><b>Ctrl+N</b></td><td>New tab</td></tr>
<tr><td><b>Ctrl+O</b></td><td>Open file</td></tr>
<tr><td><b>Ctrl+S</b></td><td>Save file</td></tr>
<tr><td><b>Ctrl+Shift+S</b></td><td>Save As</td></tr>
<tr><td><b>Ctrl+W</b></td><td>Close tab</td></tr>
<tr><td><b>Ctrl+T</b></td><td>New tab</td></tr>
<tr><td><b>Ctrl+Z</b></td><td>Undo</td></tr>
<tr><td><b>Ctrl+Y</b></td><td>Redo</td></tr>
<tr><td><b>Ctrl+X</b></td><td>Cut</td></tr>
<tr><td><b>Ctrl+C</b></td><td>Copy</td></tr>
<tr><td><b>Ctrl+V</b></td><td>Paste</td></tr>
<tr><td><b>Ctrl+A</b></td><td>Select All</td></tr>
<tr><td><b>Ctrl+F</b></td><td>Find</td></tr>
<tr><td><b>Ctrl+H</b></td><td>Find & Replace</td></tr>
<tr><td><b>Ctrl+Shift+P</b></td><td>HTML/CSS Preview</td></tr>
<tr><td><b>Ctrl+Shift+C</b></td><td>Stop execution</td></tr>
<tr><td><b>Ctrl+=</b></td><td>Zoom In</td></tr>
<tr><td><b>Ctrl+-</b></td><td>Zoom Out</td></tr>
<tr><td><b>Ctrl+0</b></td><td>Reset Zoom</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>Quit</td></tr>
</table>"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setText(shortcuts)
        msg.setStyleSheet(DARK_STYLE)
        msg.exec()

    # ── Window close ─────────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:  # type: ignore[override]
        # Check for unsaved tabs
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
                f"You have unsaved changes in:\n  • {names}\n\n"
                "These changes will be lost. Close anyway?",
                QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if reply == QMessageBox.StandardButton.Save:
                self._save_file()

        # Stop any running process
        if self._runner_thread and self._runner_thread.isRunning():
            self._runner_thread.stop_execution()
            self._runner_thread.wait(2000)

        save_settings(self._settings)
        event.accept()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="ncode",
        description="Nitin Editor — Local Code Playground",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Optional file to open",
    )
    args, _ = parser.parse_known_args()

    # Required for Wayland
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    # Disable Chromium sandbox for WebEngine if running as user
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox")

    app = QApplication(sys.argv)
    app.setApplicationName("Nitin Editor")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Nitin")
    app.setStyle("Fusion")

    # Set app icon
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))

    initial_file: Path | None = None
    if args.file:
        p = Path(args.file).resolve()
        if p.exists():
            initial_file = p

    window = NitinEditor(initial_file=initial_file)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
