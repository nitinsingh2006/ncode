"""
ncode — DSA Practice Sidebar Panel
PySide6 QWidget sidebar showing question list with search, filters, and progress.
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QListWidget, QListWidgetItem,
    QFrame, QScrollArea, QProgressBar, QSizePolicy,
)

from app.dsa.bank import Question, get_all_questions, search_questions, get_topics, get_question_count
from app.dsa.storage import get_solved_ids, get_progress, get_topic_progress, init_solutions_db


# ── Palette ──────────────────────────────────────────────────────────────────
_BG       = "#1e1e2e"
_BG2      = "#181825"
_BG3      = "#11111b"
_ACCENT   = "#89b4fa"
_GREEN    = "#a6e3a1"
_YELLOW   = "#f9e2af"
_RED      = "#f38ba8"
_TEXT     = "#cdd6f4"
_MUTED    = "#6c7086"
_BORDER   = "#313244"

_DIFF_COLORS = {
    "Easy":   _GREEN,
    "Medium": _YELLOW,
    "Hard":   _RED,
}

_SOURCE_COLORS = {
    "Striver":  "#cba6f7",
    "NeetCode": "#89dceb",
    "Both":     "#94e2d5",
}

PANEL_STYLE = f"""
QWidget#DSAPanel {{
    background: {_BG2};
    border-right: 1px solid {_BORDER};
}}
QLineEdit {{
    background: {_BG3};
    color: {_TEXT};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 12px;
}}
QLineEdit:focus {{ border-color: {_ACCENT}; }}
QComboBox {{
    background: {_BG3};
    color: {_TEXT};
    border: 1px solid {_BORDER};
    border-radius: 5px;
    padding: 3px 8px;
    font-size: 11px;
    min-width: 70px;
}}
QComboBox::drop-down {{ border: none; padding-right: 4px; }}
QComboBox QAbstractItemView {{
    background: {_BG};
    color: {_TEXT};
    selection-background-color: {_BORDER};
    border: 1px solid {_BORDER};
}}
QListWidget {{
    background: {_BG3};
    color: {_TEXT};
    border: none;
    outline: none;
    font-size: 12px;
}}
QListWidget::item {{
    padding: 7px 10px;
    border-bottom: 1px solid {_BORDER};
}}
QListWidget::item:selected {{
    background: #313244;
    color: {_TEXT};
}}
QListWidget::item:hover:!selected {{ background: #1f1f2e; }}
QPushButton#DSARefresh {{
    background: transparent;
    color: {_MUTED};
    border: none;
    font-size: 14px;
    padding: 2px;
}}
QPushButton#DSARefresh:hover {{ color: {_ACCENT}; }}
QProgressBar {{
    background: {_BG3};
    border: 1px solid {_BORDER};
    border-radius: 4px;
    height: 6px;
    text-align: center;
    font-size: 10px;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {_ACCENT};
    border-radius: 4px;
}}
QScrollArea {{ border: none; background: transparent; }}
"""


class DSAPanel(QWidget):
    """
    Left sidebar panel for DSA Practice.
    Emits question_selected(Question) when a user clicks a question.
    """
    question_selected = Signal(object)   # emits Question dataclass

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("DSAPanel")
        self.setFixedWidth(280)
        self.setStyleSheet(PANEL_STYLE)

        # State
        self._all_questions: list[Question] = []
        self._solved_ids: set[int] = set()
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)   # 300 ms debounce
        self._search_timer.timeout.connect(self._apply_filters)

        self._build_ui()
        self.refresh()

    # ── UI Build ──────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        root.addWidget(self._make_header())

        # Progress summary
        root.addWidget(self._make_progress_section())

        # Filters
        root.addWidget(self._make_filter_section())

        # Question list
        self._q_list = QListWidget()
        self._q_list.itemClicked.connect(self._on_item_clicked)
        self._q_list.itemDoubleClicked.connect(self._on_item_clicked)
        root.addWidget(self._q_list, stretch=1)

        # Footer stats
        self._footer = QLabel("0 questions")
        self._footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._footer.setStyleSheet(
            f"color:{_MUTED}; font-size:10px; padding:4px; "
            f"background:{_BG2}; border-top:1px solid {_BORDER};"
        )
        root.addWidget(self._footer)

    def _make_header(self) -> QWidget:
        hdr = QWidget()
        hdr.setFixedHeight(44)
        hdr.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 #1a1a2e, stop:1 #24273a);"
            f"border-bottom: 1px solid {_BORDER};"
        )
        hbox = QHBoxLayout(hdr)
        hbox.setContentsMargins(10, 0, 6, 0)

        icon = QLabel("🧩")
        icon.setStyleSheet("font-size: 18px;")
        hbox.addWidget(icon)

        title = QLabel("DSA Practice")
        title.setStyleSheet(
            f"color: {_ACCENT}; font-size: 13px; font-weight: bold;"
        )
        hbox.addWidget(title)
        hbox.addStretch()

        refresh_btn = QPushButton("↻")
        refresh_btn.setObjectName("DSARefresh")
        refresh_btn.setToolTip("Refresh question list and progress")
        refresh_btn.clicked.connect(self.refresh)
        hbox.addWidget(refresh_btn)

        return hdr

    def _make_progress_section(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet(
            f"background:{_BG2}; border-bottom:1px solid {_BORDER};"
        )
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(10, 8, 10, 8)
        vbox.setSpacing(4)

        top_row = QHBoxLayout()
        self._progress_label = QLabel("Loading…")
        self._progress_label.setStyleSheet(
            f"color:{_TEXT}; font-size:11px; font-weight:600;"
        )
        top_row.addWidget(self._progress_label)
        top_row.addStretch()
        self._pct_label = QLabel("")
        self._pct_label.setStyleSheet(f"color:{_ACCENT}; font-size:11px;")
        top_row.addWidget(self._pct_label)
        vbox.addLayout(top_row)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        vbox.addWidget(self._progress_bar)

        return container

    def _make_filter_section(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet(
            f"background:{_BG2}; border-bottom:1px solid {_BORDER};"
        )
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(8, 6, 8, 6)
        vbox.setSpacing(6)

        # Search
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("🔍  Search questions…")
        self._search_box.textChanged.connect(lambda _: self._search_timer.start())
        vbox.addWidget(self._search_box)

        # Filter row
        frow = QHBoxLayout()
        frow.setSpacing(4)

        self._sheet_combo = QComboBox()
        self._sheet_combo.addItems(["All Sheets", "Striver", "NeetCode"])
        self._sheet_combo.setToolTip("Filter by source sheet")
        self._sheet_combo.currentTextChanged.connect(self._apply_filters)
        frow.addWidget(self._sheet_combo)

        self._diff_combo = QComboBox()
        self._diff_combo.addItems(["All", "Easy", "Medium", "Hard"])
        self._diff_combo.setToolTip("Filter by difficulty")
        self._diff_combo.currentTextChanged.connect(self._apply_filters)
        frow.addWidget(self._diff_combo)

        self._status_combo = QComboBox()
        self._status_combo.addItems(["All", "Unsolved", "Solved"])
        self._status_combo.setToolTip("Filter by solve status")
        self._status_combo.currentTextChanged.connect(self._apply_filters)
        frow.addWidget(self._status_combo)

        vbox.addLayout(frow)

        # Topic filter
        self._topic_combo = QComboBox()
        self._topic_combo.addItem("All Topics")
        self._topic_combo.setToolTip("Filter by topic")
        self._topic_combo.currentTextChanged.connect(self._apply_filters)
        vbox.addWidget(self._topic_combo)

        return container

    # ── Data Loading ──────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Reload questions and solved status from DB."""
        try:
            init_solutions_db()
            self._all_questions = get_all_questions()
            self._solved_ids = get_solved_ids()

            # Repopulate topic combo
            topics = get_topics()
            self._topic_combo.blockSignals(True)
            current_topic = self._topic_combo.currentText()
            self._topic_combo.clear()
            self._topic_combo.addItem("All Topics")
            for t in topics:
                self._topic_combo.addItem(t)
            idx = self._topic_combo.findText(current_topic)
            if idx >= 0:
                self._topic_combo.setCurrentIndex(idx)
            self._topic_combo.blockSignals(False)

            self._update_progress()
            self._apply_filters()
        except Exception as e:
            self._footer.setText(f"Error: {e}")

    def _update_progress(self) -> None:
        total = len(self._all_questions)
        solved = len(self._solved_ids)
        pct = int(solved / total * 100) if total else 0
        self._progress_label.setText(f"Solved  {solved} / {total}")
        self._pct_label.setText(f"{pct}%")
        self._progress_bar.setValue(pct)

    def _apply_filters(self) -> None:
        query      = self._search_box.text().strip()
        sheet_raw  = self._sheet_combo.currentText()
        sheet      = "" if sheet_raw == "All Sheets" else sheet_raw
        diff       = self._diff_combo.currentText()
        status     = self._status_combo.currentText()
        topic_raw  = self._topic_combo.currentText()
        topic      = "" if topic_raw == "All Topics" else topic_raw

        try:
            questions = search_questions(
                query=query,
                sheet=sheet or "All",
                topic=topic or "All",
                difficulty=diff,
            )
        except Exception:
            questions = self._all_questions

        # Status filter
        if status == "Solved":
            questions = [q for q in questions if q.id in self._solved_ids]
        elif status == "Unsolved":
            questions = [q for q in questions if q.id not in self._solved_ids]

        self._populate_list(questions)

    def _populate_list(self, questions: list[Question]) -> None:
        self._q_list.clear()
        current_topic = None

        for q in questions:
            # Topic separator row
            if q.topic != current_topic:
                current_topic = q.topic
                sep = QListWidgetItem(f"  📂  {q.topic}")
                sep.setFlags(Qt.ItemFlag.NoItemFlags)
                sep.setForeground(QColor(_ACCENT))
                font = sep.font()
                font.setBold(True)
                font.setPointSize(10)
                sep.setFont(font)
                sep.setBackground(QColor(_BG2))
                self._q_list.addItem(sep)

            item = self._make_question_item(q)
            self._q_list.addItem(item)

        count = len(questions)
        self._footer.setText(
            f"{count} question{'s' if count != 1 else ''} shown"
        )

    def _make_question_item(self, q: Question) -> QListWidgetItem:
        solved = q.id in self._solved_ids
        tick   = "✅ " if solved else "   "
        diff_icon = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}.get(q.difficulty, "⚪")
        src_badge = {"Striver": "[S]", "NeetCode": "[N]", "Both": "[S+N]"}.get(q.source, "")

        label = f"{tick}{diff_icon}  {q.title}  {src_badge}"
        item = QListWidgetItem(label)
        item.setData(Qt.ItemDataRole.UserRole, q)
        item.setToolTip(
            f"#{q.lc_number}  {q.difficulty} · {q.topic}\n"
            f"Time: {q.time_complexity}  Space: {q.space_complexity}"
        )

        color = _DIFF_COLORS.get(q.difficulty, _TEXT)
        item.setForeground(QColor(color if not solved else _GREEN))
        return item

    # ── Interaction ───────────────────────────────────────────────────────────

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        q = item.data(Qt.ItemDataRole.UserRole)
        if q is not None:
            self.question_selected.emit(q)

    def mark_solved(self, question_id: int) -> None:
        """Call after saving a solution to update UI immediately."""
        self._solved_ids.add(question_id)
        self._update_progress()
        self._apply_filters()
