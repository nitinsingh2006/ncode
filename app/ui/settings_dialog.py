"""
Nitin Editor - ui/settings_dialog.py
Settings dialog for the editor.
"""
from __future__ import annotations

from typing import Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QFormLayout, QScrollArea, QWidget, QLineEdit,
)


DIALOG_STYLE = """
QDialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QScrollArea {
    background-color: #1e1e2e;
    border: none;
}
QGroupBox {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    margin-top: 8px;
    padding: 8px;
    color: #cba6f7;
    font-weight: bold;
    font-size: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    padding: 0 4px;
}
QLabel {
    color: #cdd6f4;
    font-size: 13px;
}
QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 120px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
}
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 6px 16px;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #45475a;
}
QPushButton[accent="true"] {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    font-weight: bold;
}
QPushButton[accent="true"]:hover {
    background-color: #74c7ec;
}
"""


class SettingsDialog(QDialog):
    settings_changed = Signal(dict)

    def __init__(self, settings: dict[str, Any], parent=None) -> None:
        super().__init__(parent)
        self._settings = dict(settings)
        self.setWindowTitle("Settings — Nitin Editor")
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setMinimumHeight(560)
        self.setStyleSheet(DIALOG_STYLE)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setSpacing(10)
        outer.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("⚙  Settings")
        title.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #89b4fa; margin-bottom: 4px;"
        )
        outer.addWidget(title)

        # Scrollable area for groups
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setSpacing(14)
        layout.setContentsMargins(0, 0, 4, 0)

        # ── Appearance ──────────────────────────────────────────────────────
        appearance_group = QGroupBox("Appearance")
        appearance_form = QFormLayout(appearance_group)
        appearance_form.setSpacing(10)

        self._theme_combo = self._make_combo(
            ["Dark", "Light"], self._settings.get("theme", "dark").capitalize()
        )
        appearance_form.addRow("Theme:", self._theme_combo)

        self._font_size_combo = self._make_combo(
            ["12", "13", "14", "15", "16", "18", "20"],
            str(self._settings.get("font_size", 14)),
        )
        appearance_form.addRow("Font Size:", self._font_size_combo)

        self._word_wrap_combo = self._make_combo(
            ["On", "Off"],
            "On" if self._settings.get("word_wrap", False) else "Off",
        )
        appearance_form.addRow("Word Wrap:", self._word_wrap_combo)
        layout.addWidget(appearance_group)

        # ── Editor ──────────────────────────────────────────────────────────
        editor_group = QGroupBox("Editor")
        editor_form = QFormLayout(editor_group)
        editor_form.setSpacing(10)

        self._tab_size_combo = self._make_combo(
            ["2", "4", "8"],
            str(self._settings.get("tab_size", 4)),
        )
        editor_form.addRow("Tab Size (spaces):", self._tab_size_combo)
        layout.addWidget(editor_group)

        # ── Execution ────────────────────────────────────────────────────────
        exec_group = QGroupBox("Execution")
        exec_form = QFormLayout(exec_group)
        exec_form.setSpacing(10)

        self._timeout_combo = self._make_combo(
            ["5", "10", "20", "30", "60"],
            str(self._settings.get("execution_timeout", 10)),
        )
        exec_form.addRow("Timeout (seconds):", self._timeout_combo)
        layout.addWidget(exec_group)

        # ── SQL ─────────────────────────────────────────────────────────────
        sql_group = QGroupBox("SQL")
        sql_form = QFormLayout(sql_group)
        sql_form.setSpacing(10)

        self._sql_db_mode_combo = self._make_combo(
            ["Temporary", "File"],
            self._settings.get("sql_db_mode", "Temporary"),
        )
        sql_form.addRow("Default database mode:", self._sql_db_mode_combo)

        self._sql_cleanup_combo = self._make_combo(
            ["Yes", "No"],
            "Yes" if self._settings.get("sql_auto_cleanup", True) else "No",
        )
        sql_form.addRow("Auto-cleanup temp databases:", self._sql_cleanup_combo)
        layout.addWidget(sql_group)

        # ── Terminal ─────────────────────────────────────────────────────────
        term_group = QGroupBox("Terminal")
        term_form = QFormLayout(term_group)
        term_form.setSpacing(10)

        self._term_os_combo = self._make_combo(
            ["Linux", "macOS", "Windows"],
            self._settings.get("terminal_default_os", "Linux"),
        )
        term_form.addRow("Default OS:", self._term_os_combo)

        self._term_timeout_combo = self._make_combo(
            ["10", "30", "60", "120"],
            str(self._settings.get("terminal_timeout", 30)),
        )
        term_form.addRow("Command timeout (s):", self._term_timeout_combo)

        self._term_history_combo = self._make_combo(
            ["100", "250", "500", "1000"],
            str(self._settings.get("terminal_history_size", 500)),
        )
        term_form.addRow("History size:", self._term_history_combo)

        self._term_confirm_combo = self._make_combo(
            ["Yes", "No"],
            "Yes" if self._settings.get("terminal_confirm_dangerous", True) else "No",
        )
        term_form.addRow("Confirm dangerous commands:", self._term_confirm_combo)
        layout.addWidget(term_group)

        # ── AI Transpiler ────────────────────────────────────────────────────
        ai_group = QGroupBox("AI Transpiler (Groq)")
        ai_form = QFormLayout(ai_group)
        ai_form.setSpacing(10)

        self._groq_key_input = QLineEdit()
        self._groq_key_input.setPlaceholderText("Paste your Groq API key (gsk_...) here…")
        self._groq_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        current_key = self._settings.get("groq_api_key") or self._settings.get("gemini_api_key", "")
        self._groq_key_input.setText(current_key)
        self._groq_key_input.setStyleSheet(
            "background: #313244; color: #cdd6f4; border: 1px solid #45475a;"
            " border-radius: 4px; padding: 4px 8px; min-width: 260px;"
        )
        ai_form.addRow("Groq API Key:", self._groq_key_input)

        hint = QLabel(
            "<small>Free & ultra-fast! Get a key at "
            "<a href='https://console.groq.com/keys' style='color:#89b4fa;'>"
            "console.groq.com/keys</a>. "
            "Leave blank to disable auto-transpilation.</small>"
        )
        hint.setOpenExternalLinks(True)
        hint.setWordWrap(True)
        ai_form.addRow("", hint)
        layout.addWidget(ai_group)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

        # ── Buttons ─────────────────────────────────────────────────────────
        button_box = QHBoxLayout()
        button_box.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_box.addWidget(cancel_btn)

        ok_btn = QPushButton("Apply & Save")
        ok_btn.setProperty("accent", "true")
        ok_btn.clicked.connect(self._apply)
        button_box.addWidget(ok_btn)

        outer.addLayout(button_box)

    def _make_combo(self, items: list[str], current: str) -> QComboBox:
        combo = QComboBox()
        for item in items:
            combo.addItem(item)
        idx = combo.findText(current)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        return combo

    def _apply(self) -> None:
        self._settings["theme"] = self._theme_combo.currentText().lower()
        self._settings["font_size"] = int(self._font_size_combo.currentText())
        self._settings["tab_size"] = int(self._tab_size_combo.currentText())
        self._settings["word_wrap"] = self._word_wrap_combo.currentText() == "On"
        self._settings["execution_timeout"] = int(self._timeout_combo.currentText())
        # SQL
        self._settings["sql_db_mode"] = self._sql_db_mode_combo.currentText()
        self._settings["sql_auto_cleanup"] = self._sql_cleanup_combo.currentText() == "Yes"
        # Terminal
        self._settings["terminal_default_os"] = self._term_os_combo.currentText()
        self._settings["terminal_timeout"] = int(self._term_timeout_combo.currentText())
        self._settings["terminal_history_size"] = int(self._term_history_combo.currentText())
        self._settings["terminal_confirm_dangerous"] = self._term_confirm_combo.currentText() == "Yes"
        # AI Transpiler
        val = self._groq_key_input.text().strip()
        self._settings["groq_api_key"] = val
        self._settings["gemini_api_key"] = val
        self.settings_changed.emit(self._settings)
        self.accept()

    def get_settings(self) -> dict[str, Any]:
        return self._settings
