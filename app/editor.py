"""
Nitin Editor - editor.py
Professional code editor widget built on PySide6 QPlainTextEdit.
Features: syntax highlighting, line numbers, current line highlight,
bracket matching, auto-indent, and all standard keyboard shortcuts.
"""
from __future__ import annotations

import re
from typing import Optional

from PySide6.QtCore import Qt, QRect, QSize, Signal, QRegularExpression
from PySide6.QtGui import (
    QColor, QFont, QPainter, QTextCharFormat, QTextCursor,
    QSyntaxHighlighter, QTextDocument, QTextOption, QKeySequence,
    QPalette, QTextFormat,
)
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit

# Always-available — no QScintilla needed
QSCI_BACKEND = None

# ── Color palette (Catppuccin Mocha-inspired dark theme) ────────────────────
C_BG = "#1e1e2e"
C_FG = "#cdd6f4"
C_LINE_HIGHLIGHT = "#2a2a3e"
C_MARGIN_BG = "#181825"
C_MARGIN_FG = "#585b70"
C_CARET = "#f38ba8"
C_SELECTION = "#313244"
C_KEYWORD = "#cba6f7"     # purple
C_STRING = "#a6e3a1"      # green
C_COMMENT = "#6c7086"     # gray
C_NUMBER = "#fab387"      # peach
C_OPERATOR = "#89dceb"    # sky blue
C_CLASS = "#f9e2af"       # yellow
C_FUNCTION = "#89b4fa"    # blue
C_PREPROCESSOR = "#f38ba8"  # red/pink
C_BUILTIN = "#cba6f7"     # purple

# ── Syntax Highlighters ──────────────────────────────────────────────────────

def _fmt(color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(color))
    if bold:
        fmt.setFontWeight(700)
    if italic:
        fmt.setFontItalic(True)
    return fmt


class PythonHighlighter(QSyntaxHighlighter):
    KEYWORDS = [
        "False", "None", "True", "and", "as", "assert", "async", "await",
        "break", "class", "continue", "def", "del", "elif", "else", "except",
        "finally", "for", "from", "global", "if", "import", "in", "is",
        "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
        "try", "while", "with", "yield",
    ]
    BUILTINS = [
        "abs", "all", "any", "bin", "bool", "bytes", "callable", "chr",
        "dict", "dir", "divmod", "enumerate", "eval", "exec", "filter",
        "float", "format", "frozenset", "getattr", "globals", "hasattr",
        "hash", "help", "hex", "id", "input", "int", "isinstance",
        "issubclass", "iter", "len", "list", "locals", "map", "max",
        "min", "next", "object", "oct", "open", "ord", "pow", "print",
        "property", "range", "repr", "reversed", "round", "set", "setattr",
        "slice", "sorted", "staticmethod", "str", "sum", "super", "tuple",
        "type", "vars", "zip",
    ]

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        kw_pat = r"\b(" + "|".join(re.escape(k) for k in self.KEYWORDS) + r")\b"
        bi_pat = r"\b(" + "|".join(re.escape(b) for b in self.BUILTINS) + r")\b"
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = [
            (QRegularExpression(kw_pat), _fmt(C_KEYWORD, bold=True)),
            (QRegularExpression(bi_pat), _fmt(C_BUILTIN)),
            (QRegularExpression(r"\bself\b"), _fmt(C_OPERATOR, italic=True)),
            (QRegularExpression(r"#[^\n]*"), _fmt(C_COMMENT, italic=True)),
            (QRegularExpression(r"\b[0-9]+\.?[0-9]*([eE][+-]?[0-9]+)?\b"), _fmt(C_NUMBER)),
            (QRegularExpression(r"0x[0-9a-fA-F]+"), _fmt(C_NUMBER)),
            (QRegularExpression(r"@\w+"), _fmt(C_PREPROCESSOR)),
            (QRegularExpression(r"\bdef\s+(\w+)"), _fmt(C_FUNCTION)),
            (QRegularExpression(r"\bclass\s+(\w+)"), _fmt(C_CLASS, bold=True)),
            (QRegularExpression(r"\"[^\"\\]*(\\.[^\"\\]*)*\""), _fmt(C_STRING)),
            (QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), _fmt(C_STRING)),
            (QRegularExpression(r"[=+\-*/<>!&|^~%]+"), _fmt(C_OPERATOR)),
        ]
        self._triple_dq = QRegularExpression(r'"""')
        self._triple_sq = QRegularExpression(r"'''")

    def highlightBlock(self, text: str) -> None:
        # Triple-quoted strings (multi-line)
        self._handle_multiline(text, self._triple_dq, 1, _fmt(C_STRING))
        self._handle_multiline(text, self._triple_sq, 2, _fmt(C_STRING))
        # Single-line rules
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)

    def _handle_multiline(
        self,
        text: str,
        delimiter: QRegularExpression,
        state: int,
        fmt: QTextCharFormat,
    ) -> None:
        start_index = 0
        if self.previousBlockState() != state:
            start_index = delimiter.match(text).capturedStart()
        while start_index >= 0:
            m = delimiter.match(text, start_index + 3 if self.previousBlockState() == state else start_index)
            if not m.hasMatch():
                self.setCurrentBlockState(state)
                length = len(text) - start_index
                self.setFormat(start_index, length, fmt)
                break
            end_index = m.capturedStart()
            length = end_index - start_index + 3
            self.setFormat(start_index, length, fmt)
            start_index = delimiter.match(text, end_index + 3).capturedStart()


class CppHighlighter(QSyntaxHighlighter):
    KEYWORDS = [
        "auto", "break", "case", "char", "class", "const", "continue",
        "default", "delete", "do", "double", "else", "enum", "explicit",
        "extern", "false", "float", "for", "friend", "goto", "if", "inline",
        "int", "long", "mutable", "namespace", "new", "nullptr", "operator",
        "override", "private", "protected", "public", "return", "short",
        "signed", "sizeof", "static", "struct", "switch", "template",
        "this", "throw", "true", "try", "typedef", "typename", "union",
        "unsigned", "using", "virtual", "void", "volatile", "while",
        "bool", "string", "vector", "map", "set", "pair", "cout", "cin",
        "endl", "std",
    ]

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        kw_pat = r"\b(" + "|".join(re.escape(k) for k in self.KEYWORDS) + r")\b"
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = [
            (QRegularExpression(kw_pat), _fmt(C_KEYWORD, bold=True)),
            (QRegularExpression(r"//[^\n]*"), _fmt(C_COMMENT, italic=True)),
            (QRegularExpression(r"#\s*\w+"), _fmt(C_PREPROCESSOR)),
            (QRegularExpression(r"\b[0-9]+\.?[0-9]*([eEfFlL]*)?\b"), _fmt(C_NUMBER)),
            (QRegularExpression(r"0x[0-9a-fA-F]+[uUlL]*"), _fmt(C_NUMBER)),
            (QRegularExpression(r"\"[^\"\\]*(\\.[^\"\\]*)*\""), _fmt(C_STRING)),
            (QRegularExpression(r"'[^'\\]*(?:\\.[^'\\]*)*'"), _fmt(C_STRING)),
            (QRegularExpression(r"\b[A-Z][A-Z0-9_]+\b"), _fmt(C_CLASS, bold=True)),
            (QRegularExpression(r"\b\w+(?=\s*\()"), _fmt(C_FUNCTION)),
            (QRegularExpression(r"[=+\-*/<>!&|^~%:]+"), _fmt(C_OPERATOR)),
        ]
        self._block_comment_start = QRegularExpression(r"/\*")
        self._block_comment_end = QRegularExpression(r"\*/")

    def highlightBlock(self, text: str) -> None:
        # Block comments
        self._handle_multiline_comment(text)
        # Single-line
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)

    def _handle_multiline_comment(self, text: str) -> None:
        fmt = _fmt(C_COMMENT, italic=True)
        start_index = 0
        if self.previousBlockState() != 1:
            m = self._block_comment_start.match(text)
            start_index = m.capturedStart() if m.hasMatch() else -1
        while start_index >= 0:
            end_m = self._block_comment_end.match(text, start_index)
            if not end_m.hasMatch():
                self.setCurrentBlockState(1)
                self.setFormat(start_index, len(text) - start_index, fmt)
                return
            end_index = end_m.capturedStart() + 2
            self.setFormat(start_index, end_index - start_index, fmt)
            m = self._block_comment_start.match(text, end_index)
            start_index = m.capturedStart() if m.hasMatch() else -1


class JavaScriptHighlighter(QSyntaxHighlighter):
    KEYWORDS = [
        "break", "case", "catch", "class", "const", "continue", "debugger",
        "default", "delete", "do", "else", "export", "extends", "false",
        "finally", "for", "function", "if", "import", "in", "instanceof",
        "let", "new", "null", "of", "return", "static", "super", "switch",
        "this", "throw", "true", "try", "typeof", "undefined", "var",
        "void", "while", "with", "yield", "async", "await", "from",
        "console", "document", "window", "require", "module", "exports",
        "Promise", "Map", "Set", "Array", "Object", "Number", "String",
        "Boolean", "Symbol",
    ]

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        kw_pat = r"\b(" + "|".join(re.escape(k) for k in self.KEYWORDS) + r")\b"
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = [
            (QRegularExpression(kw_pat), _fmt(C_KEYWORD, bold=True)),
            (QRegularExpression(r"//[^\n]*"), _fmt(C_COMMENT, italic=True)),
            (QRegularExpression(r"\b[0-9]+\.?[0-9]*([eE][+-]?[0-9]+)?\b"), _fmt(C_NUMBER)),
            (QRegularExpression(r"\"[^\"\\]*(\\.[^\"\\]*)*\""), _fmt(C_STRING)),
            (QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), _fmt(C_STRING)),
            (QRegularExpression(r"`[^`\\]*(\\.[^`\\]*)*`"), _fmt(C_STRING)),
            (QRegularExpression(r"\b\w+(?=\s*\()"), _fmt(C_FUNCTION)),
            (QRegularExpression(r"[=+\-*/<>!&|^~%]+"), _fmt(C_OPERATOR)),
        ]

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


class HTMLHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = [
            (QRegularExpression(r"<!--.*?-->"), _fmt(C_COMMENT, italic=True)),
            (QRegularExpression(r"<\s*/?\s*\w[\w\-\.]*"), _fmt(C_KEYWORD, bold=True)),
            (QRegularExpression(r">"), _fmt(C_KEYWORD, bold=True)),
            (QRegularExpression(r"\b\w[\w\-]*(?=\s*=)"), _fmt(C_FUNCTION)),
            (QRegularExpression(r"\"[^\"]*\""), _fmt(C_STRING)),
            (QRegularExpression(r"'[^']*'"), _fmt(C_STRING)),
            (QRegularExpression(r"&[\w#]+;"), _fmt(C_NUMBER)),
            (QRegularExpression(r"<!DOCTYPE[^>]*>"), _fmt(C_PREPROCESSOR)),
        ]

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


class CSSHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = [
            (QRegularExpression(r"/\*.*?\*/"), _fmt(C_COMMENT, italic=True)),
            (QRegularExpression(r"[\w\-]+(?=\s*:)"), _fmt(C_FUNCTION)),
            (QRegularExpression(r":[a-z\-]+"), _fmt(C_KEYWORD)),
            (QRegularExpression(r"::[a-z\-]+"), _fmt(C_KEYWORD)),
            (QRegularExpression(r"#[0-9a-fA-F]{3,8}\b"), _fmt(C_NUMBER)),
            (QRegularExpression(r"\b[0-9]+\.?[0-9]*(px|em|rem|%|vh|vw|pt|s|ms)?\b"), _fmt(C_NUMBER)),
            (QRegularExpression(r"\"[^\"]*\""), _fmt(C_STRING)),
            (QRegularExpression(r"'[^']*'"), _fmt(C_STRING)),
            (QRegularExpression(r"@\w+"), _fmt(C_PREPROCESSOR)),
            (QRegularExpression(r"\.[a-zA-Z][\w\-]*"), _fmt(C_CLASS)),
            (QRegularExpression(r"#[a-zA-Z][\w\-]*(?=[^0-9a-fA-F]|$)"), _fmt(C_CLASS)),
        ]

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


class SQLHighlighter(QSyntaxHighlighter):
    """SQL syntax highlighter with support for keywords, functions, strings,
    numbers, comments, and operators."""
    KEYWORDS = [
        "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE", "SET",
        "DELETE", "CREATE", "ALTER", "DROP", "TABLE", "DATABASE", "SCHEMA",
        "JOIN", "INNER", "LEFT", "RIGHT", "FULL", "OUTER", "CROSS", "ON",
        "GROUP", "BY", "ORDER", "HAVING", "LIMIT", "OFFSET", "UNION", "ALL",
        "AS", "AND", "OR", "NOT", "IN", "LIKE", "BETWEEN", "EXISTS", "IS",
        "NULL", "TRUE", "FALSE", "CASE", "WHEN", "THEN", "ELSE", "END",
        "PRIMARY", "FOREIGN", "KEY", "REFERENCES", "UNIQUE", "DEFAULT",
        "INDEX", "VIEW", "TRIGGER", "PROCEDURE", "FUNCTION", "BEGIN",
        "COMMIT", "ROLLBACK", "TRANSACTION", "WITH", "DISTINCT", "ASC", "DESC",
        "INTEGER", "TEXT", "REAL", "BLOB", "NUMERIC", "VARCHAR", "CHAR",
        "BOOLEAN", "DATE", "DATETIME", "TIMESTAMP", "FLOAT", "DOUBLE",
        "AUTOINCREMENT", "AUTO_INCREMENT", "CONSTRAINT", "CHECK", "TEMPORARY",
        "IF", "REPLACE", "IGNORE", "INTO",
    ]
    FUNCTIONS = [
        "COUNT", "SUM", "AVG", "MIN", "MAX", "COALESCE", "IFNULL", "NULLIF",
        "ROUND", "FLOOR", "CEIL", "ABS", "LENGTH", "UPPER", "LOWER", "TRIM",
        "LTRIM", "RTRIM", "SUBSTR", "SUBSTRING", "REPLACE", "INSTR", "PRINTF",
        "DATE", "TIME", "DATETIME", "JULIANDAY", "STRFTIME", "NOW", "TYPEOF",
        "CAST", "CONVERT", "GROUP_CONCAT", "RANDOM", "LAST_INSERT_ROWID",
        "CHANGES", "TOTAL_CHANGES", "ROW_NUMBER", "RANK", "DENSE_RANK",
    ]

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        kw_pat = r"\b(" + "|".join(re.escape(k) for k in self.KEYWORDS) + r")\b"
        fn_pat = r"\b(" + "|".join(re.escape(f) for f in self.FUNCTIONS) + r")(?=\s*\()\b"
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = [
            # Keywords (case-insensitive)
            (QRegularExpression(kw_pat, QRegularExpression.PatternOption.CaseInsensitiveOption),
             _fmt(C_KEYWORD, bold=True)),
            # Built-in functions
            (QRegularExpression(fn_pat, QRegularExpression.PatternOption.CaseInsensitiveOption),
             _fmt(C_FUNCTION)),
            # Line comments (-- ...)
            (QRegularExpression(r"--[^\n]*"), _fmt(C_COMMENT, italic=True)),
            # Numbers
            (QRegularExpression(r"\b[0-9]+\.?[0-9]*([eE][+-]?[0-9]+)?\b"), _fmt(C_NUMBER)),
            # Single-quoted strings
            (QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), _fmt(C_STRING)),
            # Double-quoted identifiers
            (QRegularExpression(r"\"[^\"\\]*(\\.[^\"\\]*)*\""), _fmt(C_CLASS)),
            # Backtick identifiers (MySQL-style)
            (QRegularExpression(r"`[^`]*`"), _fmt(C_CLASS)),
            # Operators
            (QRegularExpression(r"[=<>!+\-*/]+"), _fmt(C_OPERATOR)),
        ]
        # Block comments (/* ... */)
        self._block_start = QRegularExpression(r"/\*")
        self._block_end = QRegularExpression(r"\*/")

    def highlightBlock(self, text: str) -> None:
        self._handle_block_comments(text)
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)

    def _handle_block_comments(self, text: str) -> None:
        fmt = _fmt(C_COMMENT, italic=True)
        start_index = 0
        if self.previousBlockState() != 1:
            m = self._block_start.match(text)
            start_index = m.capturedStart() if m.hasMatch() else -1
        while start_index >= 0:
            end_m = self._block_end.match(text, start_index)
            if not end_m.hasMatch():
                self.setCurrentBlockState(1)
                self.setFormat(start_index, len(text) - start_index, fmt)
                return
            end_index = end_m.capturedStart() + 2
            self.setFormat(start_index, end_index - start_index, fmt)
            m = self._block_start.match(text, end_index)
            start_index = m.capturedStart() if m.hasMatch() else -1


class JavaHighlighter(QSyntaxHighlighter):
    KEYWORDS = [
        "abstract", "assert", "boolean", "break", "byte", "case", "catch",
        "char", "class", "const", "continue", "default", "do", "double",
        "else", "enum", "extends", "false", "final", "finally", "float",
        "for", "goto", "if", "implements", "import", "instanceof", "int",
        "interface", "long", "native", "new", "null", "package", "private",
        "protected", "public", "return", "short", "static", "strictfp",
        "super", "switch", "synchronized", "this", "throw", "throws",
        "transient", "true", "try", "void", "volatile", "while", "var",
        "String", "System", "out", "println", "print",
    ]

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)
        kw_pat = r"\b(" + "|".join(re.escape(k) for k in self.KEYWORDS) + r")\b"
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = [
            (QRegularExpression(kw_pat), _fmt(C_KEYWORD, bold=True)),
            (QRegularExpression(r"//[^\n]*"), _fmt(C_COMMENT, italic=True)),
            (QRegularExpression(r"\b[0-9]+\.?[0-9]*([eEfFdDlL]*)?\b"), _fmt(C_NUMBER)),
            (QRegularExpression(r"\"[^\"\\]*(\\.[^\"\\]*)*\""), _fmt(C_STRING)),
            (QRegularExpression(r"'[^'\\]*(?:\\.[^'\\]*)*'"), _fmt(C_STRING)),
            (QRegularExpression(r"@\w+"), _fmt(C_PREPROCESSOR)),
            (QRegularExpression(r"\b[A-Z]\w*\b"), _fmt(C_CLASS, bold=True)),
            (QRegularExpression(r"\b\w+(?=\s*\()"), _fmt(C_FUNCTION)),
            (QRegularExpression(r"[=+\-*/<>!&|^~%]+"), _fmt(C_OPERATOR)),
        ]
        self._block_start = QRegularExpression(r"/\*")
        self._block_end = QRegularExpression(r"\*/")

    def highlightBlock(self, text: str) -> None:
        self._handle_block_comments(text)
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)

    def _handle_block_comments(self, text: str) -> None:
        fmt = _fmt(C_COMMENT, italic=True)
        start_index = 0
        if self.previousBlockState() != 1:
            m = self._block_start.match(text)
            start_index = m.capturedStart() if m.hasMatch() else -1
        while start_index >= 0:
            end_m = self._block_end.match(text, start_index)
            if not end_m.hasMatch():
                self.setCurrentBlockState(1)
                self.setFormat(start_index, len(text) - start_index, fmt)
                return
            end_index = end_m.capturedStart() + 2
            self.setFormat(start_index, end_index - start_index, fmt)
            m = self._block_start.match(text, end_index)
            start_index = m.capturedStart() if m.hasMatch() else -1


HIGHLIGHTER_MAP: dict[str, type] = {
    "Python": PythonHighlighter,
    "C": CppHighlighter,
    "C++": CppHighlighter,
    "Java": JavaHighlighter,
    "JavaScript": JavaScriptHighlighter,
    "HTML": HTMLHighlighter,
    "CSS": CSSHighlighter,
    "SQL": SQLHighlighter,
}


# ── Line number area ─────────────────────────────────────────────────────────

class LineNumberArea(QWidget):
    def __init__(self, editor: "CodeEditor") -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor._line_number_area_width(), 0)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        self._editor._paint_line_numbers(event)


# ── Main code editor widget ───────────────────────────────────────────────────

class CodeEditor(QPlainTextEdit):
    """
    Professional code editor with:
    - Syntax highlighting (custom QSyntaxHighlighter per language)
    - Line numbers
    - Current line highlighting
    - Bracket matching indicators
    - Auto-indent
    - Tab → 4 spaces
    - All standard keyboard shortcuts
    - Ctrl+Enter → run
    """
    run_requested = Signal()
    cursor_position_changed = Signal(int, int)

    # Opening/closing bracket pairs for matching
    OPEN_BRACKETS = "([{"
    CLOSE_BRACKETS = ")]}"
    BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}"}
    REVERSE_PAIRS = {")": "(", "]": "[", "}": "{"}

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._highlighter: Optional[QSyntaxHighlighter] = None
        self._line_area = LineNumberArea(self)
        self._tab_size = 4
        self._font_size = 14

        self._setup_appearance()
        self._connect_signals()

    def _setup_appearance(self) -> None:
        # Dark theme via palette + stylesheet
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {C_BG};
                color: {C_FG};
                border: none;
                selection-background-color: {C_SELECTION};
                selection-color: {C_FG};
            }}
        """)
        # Monospace font
        font = QFont()
        font.setFamilies(["JetBrains Mono", "Fira Code", "Consolas", "Courier New", "monospace"])
        font.setPointSize(self._font_size)
        font.setFixedPitch(True)
        self.setFont(font)
        # Tab stop
        fm = self.fontMetrics()
        self.setTabStopDistance(fm.horizontalAdvance(" ") * self._tab_size)
        # Word wrap off
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        # Line number area margin
        self.setViewportMargins(self._line_number_area_width(), 0, 0, 0)

    def _connect_signals(self) -> None:
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._on_cursor_changed)
        self.cursorPositionChanged.connect(self._highlight_current_line)

    # ── Line numbers ──────────────────────────────────────────────────────────

    def _line_number_area_width(self) -> int:
        digits = max(1, len(str(max(1, self.blockCount()))))
        return 8 + self.fontMetrics().horizontalAdvance("9") * (digits + 1)

    def _update_line_number_area_width(self, _: int) -> None:
        self.setViewportMargins(self._line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self._line_area.scroll(0, dy)
        else:
            self._line_area.update(0, rect.y(), self._line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_area.setGeometry(
            QRect(cr.left(), cr.top(), self._line_number_area_width(), cr.height())
        )

    def _paint_line_numbers(self, event) -> None:  # type: ignore[type-arg]
        painter = QPainter(self._line_area)
        painter.fillRect(event.rect(), QColor(C_MARGIN_BG))

        # Separator line
        painter.setPen(QColor("#313244"))
        painter.drawLine(
            self._line_area.width() - 1, event.rect().top(),
            self._line_area.width() - 1, event.rect().bottom()
        )

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + int(self.blockBoundingRect(block).height())
        current_line = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                is_current = block_number == current_line
                color = QColor("#cdd6f4") if is_current else QColor(C_MARGIN_FG)
                painter.setPen(color)
                if is_current:
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                else:
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)
                painter.drawText(
                    0, top,
                    self._line_area.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    # ── Current line highlight ────────────────────────────────────────────────

    def _highlight_current_line(self) -> None:
        extra: list[QTextEdit.ExtraSelection] = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor(C_LINE_HIGHLIGHT))
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extra.append(sel)
        self.setExtraSelections(extra)

    def _on_cursor_changed(self) -> None:
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.cursor_position_changed.emit(line, col)

    # ── Key handling ──────────────────────────────────────────────────────────

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        # Ctrl+Enter → run
        if (
            event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.run_requested.emit()
            return

        # Tab → spaces
        if event.key() == Qt.Key.Key_Tab and not event.modifiers():
            self._insert_spaces()
            return

        # Shift+Tab → unindent
        if event.key() == Qt.Key.Key_Backtab:
            self._unindent()
            return

        # Enter → auto-indent
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not event.modifiers():
            self._handle_return()
            return

        # Auto-close brackets
        if event.text() in self.BRACKET_PAIRS:
            super().keyPressEvent(event)
            self.insertPlainText(self.BRACKET_PAIRS[event.text()])
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
            return

        # Skip over closing bracket if already there
        if event.text() in self.CLOSE_BRACKETS:
            cursor = self.textCursor()
            doc = self.document()
            next_char = doc.characterAt(cursor.position())
            if next_char == event.text():
                cursor.movePosition(QTextCursor.MoveOperation.Right)
                self.setTextCursor(cursor)
                return

        # Backspace → remove auto-inserted bracket
        if event.key() == Qt.Key.Key_Backspace:
            cursor = self.textCursor()
            if not cursor.hasSelection():
                doc = self.document()
                pos = cursor.position()
                if pos > 0:
                    prev_char = doc.characterAt(pos - 1)
                    next_char = doc.characterAt(pos)
                    if prev_char in self.BRACKET_PAIRS and self.BRACKET_PAIRS[prev_char] == next_char:
                        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
                        cursor.removeSelectedText()

        super().keyPressEvent(event)

    def _insert_spaces(self) -> None:
        cursor = self.textCursor()
        col = cursor.columnNumber()
        spaces_to_add = self._tab_size - (col % self._tab_size)
        self.insertPlainText(" " * spaces_to_add)

    def _unindent(self) -> None:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.KeepAnchor,
            min(self._tab_size, len(cursor.block().text()) - len(cursor.block().text().lstrip()))
        )
        selected = cursor.selectedText()
        if selected and all(c == " " for c in selected):
            cursor.removeSelectedText()

    def _handle_return(self) -> None:
        cursor = self.textCursor()
        block_text = cursor.block().text()
        # Calculate current indentation
        indent = ""
        for ch in block_text:
            if ch == " ":
                indent += " "
            elif ch == "\t":
                indent += "\t"
            else:
                break
        # Extra indent after block-opening characters
        stripped = block_text.rstrip()
        if stripped and stripped[-1] in "{:([":
            indent += " " * self._tab_size
        # Insert newline + indent
        cursor.insertText("\n" + indent)
        self.setTextCursor(cursor)

    # ── Language and appearance ───────────────────────────────────────────────

    def set_language(self, language: str) -> None:
        # Remove old highlighter
        if self._highlighter:
            self._highlighter.setDocument(None)
            self._highlighter = None
        # Apply new highlighter
        HighlighterClass = HIGHLIGHTER_MAP.get(language)
        if HighlighterClass:
            self._highlighter = HighlighterClass(self.document())

    def set_font_size(self, size: int) -> None:
        self._font_size = size
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)
        fm = self.fontMetrics()
        self.setTabStopDistance(fm.horizontalAdvance(" ") * self._tab_size)
        self._update_line_number_area_width(0)

    def set_tab_size(self, size: int) -> None:
        self._tab_size = size
        fm = self.fontMetrics()
        self.setTabStopDistance(fm.horizontalAdvance(" ") * size)

    def set_word_wrap(self, enabled: bool) -> None:
        mode = (
            QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere
            if enabled
            else QTextOption.WrapMode.NoWrap
        )
        self.setWordWrapMode(mode)

    def get_text(self) -> str:
        return self.toPlainText()

    def set_text(self, text: str) -> None:
        self.setPlainText(text)

    def get_cursor_position(self) -> tuple[int, int]:
        cursor = self.textCursor()
        return cursor.blockNumber() + 1, cursor.columnNumber() + 1

    # Expose text_changed as a compatible signal alias
    @property
    def text_changed(self):
        return self.textChanged


# ── Public factory ────────────────────────────────────────────────────────────

def make_editor(parent: Optional[QWidget] = None) -> CodeEditor:
    """Create and return a CodeEditor instance."""
    return CodeEditor(parent)
