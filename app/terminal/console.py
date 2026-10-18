"""
Nitin Editor - console.py
Integrated interactive terminal console widget built on PySide6 QPlainTextEdit.
Features:
- Immutable stdout/stderr history protection
- Inline interactive stdin typing at prompt position
- Real-time streaming of stdout, stderr, and system banners
- Protected backspace, delete, home, and arrow navigation
- Native selection & copy support
- Signal-driven Enter (stdin submission), Ctrl+C (interrupt), and Ctrl+D (EOF)
"""
from __future__ import annotations

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QColor, QTextCharFormat, QTextCursor, QFont, QKeyEvent
)
from PySide6.QtWidgets import QPlainTextEdit, QWidget

# Catppuccin Mocha colors
COLOR_STDOUT = "#cdd6f4"
COLOR_STDERR = "#f38ba8"
COLOR_STDIN = "#a6e3a1"
COLOR_STATUS = "#89b4fa"
COLOR_WARN = "#f9e2af"
COLOR_BG = "#11111b"


class TerminalConsole(QPlainTextEdit):
    """
    Interactive Terminal Console widget.
    Provides inline typing at current stdout/stderr prompt position while
    protecting past output history as read-only.
    
    Signals:
      - input_submitted(str): Emitted when user presses Enter on active input line
      - interrupt_requested(): Emitted on Ctrl+C (when no text is selected)
      - eof_requested(): Emitted on Ctrl+D
    """
    input_submitted = Signal(str)
    interrupt_requested = Signal()
    eof_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setUndoRedoEnabled(False)
        self.setStyleSheet(
            f"QPlainTextEdit {{ background:{COLOR_BG}; color:{COLOR_STDOUT}; border:none; padding:8px; "
            f"font-family:'JetBrains Mono','Fira Code','Consolas','Courier New',monospace; font-size:12px; }}"
        )
        self.document().setMaximumBlockCount(5000)

        # Output boundary position in document (0-indexed char count)
        # Text before this position is read-only past terminal history.
        self._output_boundary: int = 0
        
        # History for shell commands when process is idle
        self._history: list[str] = []
        self._history_pos: int = -1
        self._draft_input: str = ""

    def append_stdout(self, text: str) -> None:
        self._append_chunk(text, COLOR_STDOUT)

    def append_stderr(self, text: str) -> None:
        self._append_chunk(text, COLOR_STDERR)

    def append_status(self, text: str, color: str = COLOR_STATUS) -> None:
        self._append_chunk(text, color)

    def _append_chunk(self, text: str, color: str) -> None:
        """
        Append output chunk at boundary, preserving any uncommitted draft input at document end.
        """
        doc = self.document()
        cursor = self.textCursor()
        
        # Clamp boundary to document length
        current_len = max(0, doc.characterCount() - 1)
        if self._output_boundary > current_len:
            self._output_boundary = current_len

        # Extract any uncommitted user input typed after boundary
        draft_input = ""
        if current_len > self._output_boundary:
            cursor.setPosition(self._output_boundary)
            cursor.setPosition(current_len, QTextCursor.MoveMode.KeepAnchor)
            draft_input = cursor.selectedText()
            cursor.removeSelectedText()

        # Insert new output chunk at boundary
        cursor.setPosition(self._output_boundary)
        fmt = cursor.charFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        
        # Update output boundary to end of new output chunk
        self._output_boundary = cursor.position()

        # Re-insert draft input if present
        if draft_input:
            fmt_in = cursor.charFormat()
            fmt_in.setForeground(QColor(COLOR_STDIN))
            cursor.setCharFormat(fmt_in)
            cursor.insertText(draft_input)

        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def clear(self) -> None:
        super().clear()
        self._output_boundary = 0
        self._history_pos = -1

    def clear_terminal(self) -> None:
        self.clear()

    def get_current_input(self) -> str:
        doc = self.document()
        current_len = doc.characterCount() - 1
        if current_len > self._output_boundary:
            cursor = self.textCursor()
            cursor.setPosition(self._output_boundary)
            cursor.setPosition(current_len, QTextCursor.MoveMode.KeepAnchor)
            return cursor.selectedText()
        return ""

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        mods = event.modifiers()
        ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)

        # 1. Ctrl+C handler
        if key == Qt.Key.Key_C and ctrl:
            if self.textCursor().hasSelection():
                super().keyPressEvent(event)
                return
            self.interrupt_requested.emit()
            return

        # 2. Ctrl+D handler
        if key == Qt.Key.Key_D and ctrl:
            self.eof_requested.emit()
            return

        # 3. Enter / Return key handler
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            typed = self.get_current_input()
            
            # Commit typed text and append newline
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText("\n")
            self._output_boundary = cursor.position()
            self.setTextCursor(cursor)
            self.ensureCursorVisible()

            self._history_pos = -1
            self.input_submitted.emit(typed)
            return

        # 4. Backspace handler
        if key == Qt.Key.Key_Backspace:
            cursor = self.textCursor()
            if cursor.hasSelection():
                if cursor.selectionStart() >= self._output_boundary:
                    super().keyPressEvent(event)
                return
            if cursor.position() > self._output_boundary:
                super().keyPressEvent(event)
            return

        # 5. Delete key handler
        if key == Qt.Key.Key_Delete:
            cursor = self.textCursor()
            if cursor.position() >= self._output_boundary:
                super().keyPressEvent(event)
            return

        # 6. Left arrow navigation handler
        if key == Qt.Key.Key_Left:
            cursor = self.textCursor()
            if cursor.position() > self._output_boundary:
                super().keyPressEvent(event)
            return

        # 7. Home key handler
        if key == Qt.Key.Key_Home:
            cursor = self.textCursor()
            cursor.setPosition(self._output_boundary)
            self.setTextCursor(cursor)
            return

        # 8. Up / Down arrow history navigation (when idle/drafting)
        if key == Qt.Key.Key_Up:
            self._history_up()
            return
        if key == Qt.Key.Key_Down:
            self._history_down()
            return

        # 9. Printable text entry
        if event.text():
            cursor = self.textCursor()
            # If cursor is inside immutable output area, snap cursor to document end before typing
            if cursor.position() < self._output_boundary:
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.setTextCursor(cursor)

            fmt = cursor.charFormat()
            fmt.setForeground(QColor(COLOR_STDIN))
            cursor.setCharFormat(fmt)
            super().keyPressEvent(event)

    def set_input_text(self, text: str) -> None:
        """Programmatically set current active input line (e.g. history navigation)."""
        doc = self.document()
        current_len = doc.characterCount() - 1
        cursor = self.textCursor()
        cursor.setPosition(self._output_boundary)
        cursor.setPosition(current_len, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        
        if text:
            fmt = cursor.charFormat()
            fmt.setForeground(QColor(COLOR_STDIN))
            cursor.setCharFormat(fmt)
            cursor.insertText(text)
            
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def set_history(self, history_list: list[str]) -> None:
        self._history = history_list

    def _history_up(self) -> None:
        if not self._history:
            return
        if self._history_pos == -1:
            self._draft_input = self.get_current_input()
        self._history_pos = min(self._history_pos + 1, len(self._history) - 1)
        self.set_input_text(self._history[self._history_pos])

    def _history_down(self) -> None:
        if self._history_pos <= 0:
            self._history_pos = -1
            self.set_input_text(self._draft_input)
            return
        self._history_pos -= 1
        self.set_input_text(self._history[self._history_pos])
