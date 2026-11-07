"""
ncode — Pomodoro Timer Widget
Built-in focus timer: 25 min work / 5 min break / 15 min long break.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QApplication, QMessageBox, QSizePolicy,
)

# ── Defaults ──────────────────────────────────────────────────────────────────
_DEFAULT_WORK       = 25   # minutes
_DEFAULT_BREAK      = 5    # minutes
_DEFAULT_LONG_BREAK = 15   # minutes
_POMODOROS_BEFORE_LONG_BREAK = 4

# ── Palette ───────────────────────────────────────────────────────────────────
_BG       = "#1e1e2e"
_BG2      = "#181825"
_BORDER   = "#313244"
_TEXT     = "#cdd6f4"
_MUTED    = "#6c7086"
_WORK_CLR = "#f38ba8"   # tomato / red
_BREAK_CLR= "#a6e3a1"   # green
_ACCENT   = "#89b4fa"

POMO_STYLE = f"""
QWidget#PomodoroWidget {{
    background: {_BG2};
}}
QPushButton#PomoBtn {{
    background: {_BORDER};
    color: {_TEXT};
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-size: 13px;
    font-weight: bold;
}}
QPushButton#PomoBtn:hover {{
    background: #45475a;
}}
QPushButton#PomoBtn:disabled {{
    color: {_MUTED};
}}
"""


class PomodoroWidget(QWidget):
    """
    Self-contained Pomodoro focus timer widget.

    Settings keys (read from parent's settings dict via set_settings()):
        pomodoro_work_duration      – work session in minutes (default 25)
        pomodoro_break_duration     – short break in minutes  (default 5)
        pomodoro_long_break_duration– long break in minutes   (default 15)
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("PomodoroWidget")
        self.setStyleSheet(POMO_STYLE)

        # Configuration
        self._work_min       = _DEFAULT_WORK
        self._break_min      = _DEFAULT_BREAK
        self._long_break_min = _DEFAULT_LONG_BREAK

        # State
        self._is_work_session = True    # True = work, False = break
        self._pomodoro_count  = 0       # completed work sessions
        self._seconds_left    = self._work_min * 60
        self._running         = False

        # QTimer (fires every second)
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        self._build_ui()
        self._refresh_display()

    # ── Settings ──────────────────────────────────────────────────────────────

    def set_settings(self, settings: dict) -> None:
        """Apply settings from the main app settings dict."""
        self._work_min       = settings.get("pomodoro_work_duration",       _DEFAULT_WORK)
        self._break_min      = settings.get("pomodoro_break_duration",      _DEFAULT_BREAK)
        self._long_break_min = settings.get("pomodoro_long_break_duration", _DEFAULT_LONG_BREAK)
        # Reset if not running so new durations take effect
        if not self._running:
            self._seconds_left = self._work_min * 60
            self._refresh_display()

    # ── UI Build ──────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Session type label
        self._session_label = QLabel("🍅  FOCUS SESSION")
        self._session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._session_label.setStyleSheet(
            f"color: {_WORK_CLR}; font-size: 14px; font-weight: bold; letter-spacing: 1px;"
        )
        root.addWidget(self._session_label)

        # Big countdown display
        self._time_label = QLabel("25:00")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(52)
        font.setBold(True)
        font.setFamily("monospace")
        self._time_label.setFont(font)
        self._time_label.setStyleSheet(f"color: {_WORK_CLR}; letter-spacing: 2px;")
        root.addWidget(self._time_label)

        # Pomodoro count
        self._count_label = QLabel("🍅 ×0")
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_label.setStyleSheet(f"color: {_MUTED}; font-size: 16px;")
        root.addWidget(self._count_label)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._start_btn = QPushButton("▶  Start")
        self._start_btn.setObjectName("PomoBtn")
        self._start_btn.clicked.connect(self._on_start_pause)
        btn_row.addWidget(self._start_btn)

        self._reset_btn = QPushButton("↺  Reset")
        self._reset_btn.setObjectName("PomoBtn")
        self._reset_btn.clicked.connect(self._on_reset)
        btn_row.addWidget(self._reset_btn)

        root.addLayout(btn_row)

        # Skip button
        self._skip_btn = QPushButton("⏭  Skip Session")
        self._skip_btn.setObjectName("PomoBtn")
        self._skip_btn.clicked.connect(self._skip_session)
        root.addWidget(self._skip_btn)

        # Info label
        self._info_label = QLabel("Work 25 min → Break 5 min → Long break every 4 🍅")
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet(f"color: {_MUTED}; font-size: 11px;")
        root.addWidget(self._info_label)

        root.addStretch()

    # ── Timer Logic ───────────────────────────────────────────────────────────

    def _tick(self) -> None:
        """Called every second by QTimer."""
        self._seconds_left -= 1
        self._refresh_display()

        if self._seconds_left <= 0:
            self._timer.stop()
            self._running = False
            self._on_session_end()

    def _on_session_end(self) -> None:
        """Handle end of a session: beep, notify, switch."""
        QApplication.beep()

        if self._is_work_session:
            self._pomodoro_count += 1
            self._count_label.setText(f"🍅 ×{self._pomodoro_count}")
            if self._pomodoro_count % _POMODOROS_BEFORE_LONG_BREAK == 0:
                next_name = "Long Break"
                next_secs = self._long_break_min * 60
            else:
                next_name = "Short Break"
                next_secs = self._break_min * 60
            msg = f"🍅 Work session complete!\nStarting {next_name} ({next_secs // 60} min)."
        else:
            next_name = "Work Session"
            next_secs = self._work_min * 60
            msg = "✅ Break over!\nTime to focus — starting Work Session."

        # Show notification
        box = QMessageBox(self)
        box.setWindowTitle("Pomodoro Timer")
        box.setText(msg)
        box.setStyleSheet(
            "QMessageBox { background:#1e1e2e; color:#cdd6f4; }"
            "QLabel { color:#cdd6f4; font-size:13px; }"
            "QPushButton { background:#313244; color:#cdd6f4; padding:5px 16px; border-radius:4px; }"
        )
        box.exec()

        # Switch session
        self._is_work_session = not self._is_work_session
        self._seconds_left = next_secs
        self._refresh_display()
        # Auto-start next session
        self._timer.start()
        self._running = True
        self._start_btn.setText("⏸  Pause")

    def _on_start_pause(self) -> None:
        if self._running:
            self._timer.stop()
            self._running = False
            self._start_btn.setText("▶  Start")
        else:
            self._timer.start()
            self._running = True
            self._start_btn.setText("⏸  Pause")

    def _on_reset(self) -> None:
        self._timer.stop()
        self._running = False
        self._is_work_session = True
        self._pomodoro_count = 0
        self._seconds_left = self._work_min * 60
        self._start_btn.setText("▶  Start")
        self._count_label.setText("🍅 ×0")
        self._refresh_display()

    def _skip_session(self) -> None:
        """Skip remaining time in current session."""
        self._timer.stop()
        self._running = False
        self._seconds_left = 0
        self._on_session_end()

    # ── Display ───────────────────────────────────────────────────────────────

    def _refresh_display(self) -> None:
        mins, secs = divmod(max(0, self._seconds_left), 60)
        self._time_label.setText(f"{mins:02d}:{secs:02d}")

        if self._is_work_session:
            self._session_label.setText("🍅  FOCUS SESSION")
            self._session_label.setStyleSheet(
                f"color: {_WORK_CLR}; font-size: 14px; font-weight: bold; letter-spacing: 1px;"
            )
            self._time_label.setStyleSheet(f"color: {_WORK_CLR}; letter-spacing: 2px;")
        else:
            lbl = "☕  LONG BREAK" if (
                self._pomodoro_count % _POMODOROS_BEFORE_LONG_BREAK == 0
                and self._pomodoro_count > 0
            ) else "🌿  BREAK TIME"
            self._session_label.setText(lbl)
            self._session_label.setStyleSheet(
                f"color: {_BREAK_CLR}; font-size: 14px; font-weight: bold; letter-spacing: 1px;"
            )
            self._time_label.setStyleSheet(f"color: {_BREAK_CLR}; letter-spacing: 2px;")
