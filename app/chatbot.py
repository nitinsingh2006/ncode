"""
ncode — Live Groq Chatbot Panel
A side-panel chatbot that is always aware of the currently open tab's code,
filename, and language. The user can ask questions in Hindi or English.
Uses the same urllib-only Groq pattern as the rest of the project.

Code blocks rendered as real widgets with copy-to-clipboard button (top-right corner),
just like ChatGPT / Claude web interface.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from PySide6.QtCore import Qt, Signal as Sig, QObject, QThread, QTimer
from PySide6.QtGui import QTextOption, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QPlainTextEdit, QLineEdit, QPushButton, QLabel, QFrame,
    QSizePolicy, QApplication,
)

# ── Groq config (same as rest of app) ────────────────────────────────────────
_GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL = "qwen/qwen3.8-27b"

_SYSTEM_PROMPT = (
    "You are a helpful coding assistant embedded inside 'ncode' — a desktop code editor. "
    "The user may speak in Hindi, English, or Hinglish. Always reply in the same language they used. "
    "Keep answers concise and practical. "
    "If code context is provided, use it to give accurate, specific answers. "
    "Do NOT output the user's full code back unless they explicitly ask. "
    "Format code snippets with triple backticks."
)


# ── Background worker ─────────────────────────────────────────────────────────
class _GroqWorker(QObject):
    """Runs a single Groq request on a background QThread."""
    finished = Sig(str)   # reply text
    errored  = Sig(str)   # error message

    def __init__(self, api_key: str, messages: list[dict]) -> None:
        super().__init__()
        self._api_key = api_key
        self._messages = messages

    def run(self) -> None:
        try:
            payload = {
                "model": _GROQ_MODEL,
                "messages": self._messages,
                "temperature": 0.7,
                "max_tokens": 1024,
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                _GROQ_URL, data=data,
                headers={
                    "Content-Type":  "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    ),
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            reply = result["choices"][0]["message"]["content"].strip()
            self.finished.emit(reply)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                self.errored.emit("❌ Groq API key invalid. Settings → Preferences mein key daalo.")
            elif e.code == 429:
                self.errored.emit("⚠️ Rate limit hit. Thoda wait karo aur phir try karo.")
            elif e.code == 404:
                self.errored.emit("❌ Groq model not found. API key ke saath available model check karo.")
            else:
                self.errored.emit(f"❌ Groq HTTP {e.code} error.")
        except urllib.error.URLError:
            self.errored.emit("❌ Network error — internet check karo.")
        except Exception as e:  # noqa: BLE001
            self.errored.emit(f"❌ Error: {e}")


# ── Code Block Widget (with copy button) ──────────────────────────────────────
class _CodeBlockWidget(QWidget):
    """
    Renders a single fenced code block with:
    - A header bar showing the language name + copy-to-clipboard button (top-right)
    - A read-only QPlainTextEdit showing the code
    """

    def __init__(self, code: str, lang: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._code = code
        self._copied_timer: QTimer | None = None
        self._build(lang)

    def _build(self, lang: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header bar ──
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background:#11111b; border-radius:6px 6px 0 0; border:none; }"
        )
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(10, 5, 8, 5)

        lang_lbl = QLabel(lang.lower() if lang else "code")
        lang_lbl.setStyleSheet("color:#6c7086; font-size:10px; font-family:monospace;")
        hlay.addWidget(lang_lbl)
        hlay.addStretch()

        self._copy_btn = QPushButton("⧉  Copy")
        self._copy_btn.setFixedHeight(22)
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.setStyleSheet(
            "QPushButton {"
            "  background: transparent; color:#89b4fa;"
            "  border:1px solid #313244; border-radius:4px;"
            "  padding: 0 8px; font-size:10px; font-weight:bold;"
            "}"
            "QPushButton:hover { background:#313244; color:#cdd6f4; }"
        )
        self._copy_btn.clicked.connect(self._copy_code)
        hlay.addWidget(self._copy_btn)
        layout.addWidget(header)

        # ── Code area ──
        code_edit = QPlainTextEdit(self._code)
        code_edit.setReadOnly(True)
        code_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        code_edit.setStyleSheet(
            "QPlainTextEdit {"
            "  background:#11111b; color:#89b4fa;"
            "  font-family: 'Courier New', monospace; font-size:11px;"
            "  border:none; border-radius:0 0 6px 6px;"
            "  padding:10px;"
            "}"
            "QScrollBar:horizontal { height:6px; background:#1e1e2e; }"
            "QScrollBar::handle:horizontal { background:#45475a; border-radius:3px; }"
        )
        # Fit height to content (max 300px)
        lines = self._code.count("\n") + 1
        line_h = code_edit.fontMetrics().height()
        target_h = min(lines * line_h + 24, 300)
        code_edit.setFixedHeight(target_h)
        layout.addWidget(code_edit)

    def _copy_code(self) -> None:
        QGuiApplication.clipboard().setText(self._code)
        self._copy_btn.setText("✓  Copied!")
        self._copy_btn.setStyleSheet(
            "QPushButton {"
            "  background:#a6e3a1; color:#1e1e2e;"
            "  border:none; border-radius:4px;"
            "  padding: 0 8px; font-size:10px; font-weight:bold;"
            "}"
        )
        # Reset after 2s
        if self._copied_timer:
            self._copied_timer.stop()
        self._copied_timer = QTimer()
        self._copied_timer.setSingleShot(True)
        self._copied_timer.timeout.connect(self._reset_copy_btn)
        self._copied_timer.start(2000)

    def _reset_copy_btn(self) -> None:
        self._copy_btn.setText("⧉  Copy")
        self._copy_btn.setStyleSheet(
            "QPushButton {"
            "  background: transparent; color:#89b4fa;"
            "  border:1px solid #313244; border-radius:4px;"
            "  padding: 0 8px; font-size:10px; font-weight:bold;"
            "}"
            "QPushButton:hover { background:#313244; color:#cdd6f4; }"
        )


# ── Single message bubble widget ──────────────────────────────────────────────
class _BubbleWidget(QWidget):
    """
    One chat message. Parses text + fenced code blocks and renders them
    as a mix of QLabel (text) and _CodeBlockWidget (code blocks).
    """

    def __init__(self, role: str, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._role = role
        self._build(text)

    def _build(self, text: str) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 2, 0, 2)
        outer.setSpacing(0)

        if self._role == "user":
            # Right-aligned purple bubble — wrap in HBox with stretch on left
            wrap = QHBoxLayout()
            wrap.setContentsMargins(30, 0, 0, 0)
            wrap.addStretch()
            lbl = QLabel()
            lbl.setTextFormat(Qt.TextFormat.RichText)
            lbl.setWordWrap(True)
            lbl.setOpenExternalLinks(False)
            safe = self._escape(text)
            safe = self._render_inline(safe)
            safe = safe.replace("\n", "<br>")
            lbl.setText(safe)
            lbl.setStyleSheet(
                "QLabel {"
                "  background:#7c3aed; color:#ffffff;"
                "  border-radius:18px 18px 4px 18px;"
                "  padding:10px 14px; font-size:12px; line-height:1.5;"
                "}"
            )
            lbl.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Preferred,
            )
            lbl.setMaximumWidth(400)
            wrap.addWidget(lbl)
            outer.addLayout(wrap)
            return

        if self._role in ("system",):
            # Centered subtle label
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(
                "color:#6c7086; font-size:10px; font-style:italic;"
                "background:#181825; border-radius:8px; padding:4px 10px;"
            )
            outer.addWidget(lbl)
            return

        # ── AI / error / thinking bubbles ── left-aligned card ──
        card_frame = QFrame()
        if self._role == "error":
            card_style = "QFrame{background:#2d1b1b;border-radius:4px 18px 18px 18px;border-left:3px solid #f38ba8;}"
        elif self._role == "thinking":
            card_style = "QFrame{background:#1e1e2e;border-radius:4px 18px 18px 18px;border-left:3px solid #fab387;}"
        else:
            card_style = "QFrame{background:#1a2332;border-radius:4px 18px 18px 18px;border-left:3px solid #a6e3a1;}"
        card_frame.setStyleSheet(card_style)

        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(6)

        # Role label (small, above content)
        if self._role == "assistant":
            role_lbl = QLabel("🤖 AI")
            role_lbl.setStyleSheet(
                "color:#a6e3a1; font-weight:bold; font-size:10px;"
                "letter-spacing:1px; background:transparent;"
            )
            card_layout.addWidget(role_lbl)
        elif self._role == "error":
            role_lbl = QLabel("⚠ Error")
            role_lbl.setStyleSheet("color:#f38ba8; font-weight:bold; font-size:10px; background:transparent;")
            card_layout.addWidget(role_lbl)
        elif self._role == "thinking":
            role_lbl = QLabel("⏳ Thinking...")
            role_lbl.setStyleSheet("color:#fab387; font-style:italic; font-size:11px; background:transparent;")
            card_layout.addWidget(role_lbl)

        if self._role != "thinking":
            # Parse text and code blocks, render in order
            segments = self._parse_segments(text)
            for kind, content, lang in segments:
                if kind == "code":
                    cb = _CodeBlockWidget(content, lang)
                    card_layout.addWidget(cb)
                else:
                    if content.strip():
                        lbl = QLabel()
                        lbl.setTextFormat(Qt.TextFormat.RichText)
                        lbl.setWordWrap(True)
                        lbl.setOpenExternalLinks(True)
                        safe = self._escape(content)
                        safe = self._render_inline(safe)
                        safe = safe.replace("\n", "<br>")
                        color = "#f38ba8" if self._role == "error" else "#cdd6f4"
                        lbl.setText(f'<span style="color:{color};font-size:12px;line-height:1.6;">{safe}</span>')
                        lbl.setStyleSheet("background:transparent;")
                        lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                        card_layout.addWidget(lbl)

        wrap2 = QHBoxLayout()
        wrap2.setContentsMargins(0, 0, 30, 0)
        wrap2.addWidget(card_frame)
        wrap2.addStretch()
        outer.addLayout(wrap2)

    # ── Helpers ──

    @staticmethod
    def _parse_segments(text: str) -> list[tuple[str, str, str]]:
        """Split text into alternating ('text', ..., '') and ('code', ..., lang) segments."""
        pattern = re.compile(r"```(\w*)\n?(.*?)```", re.DOTALL)
        segments: list[tuple[str, str, str]] = []
        last = 0
        for m in pattern.finditer(text):
            if m.start() > last:
                segments.append(("text", text[last:m.start()], ""))
            lang = m.group(1).strip()
            code = m.group(2)
            segments.append(("code", code, lang))
            last = m.end()
        if last < len(text):
            segments.append(("text", text[last:], ""))
        return segments

    @staticmethod
    def _escape(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @staticmethod
    def _render_inline(s: str) -> str:
        """Render inline `code` and **bold**."""
        # Inline code
        s = re.sub(
            r"`([^`]+)`",
            r'<code style="background:#313244;color:#f38ba8;padding:1px 5px;'
            r'border-radius:3px;font-size:11px;">\1</code>',
            s,
        )
        # Bold
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        return s


# ── Main Chat Panel widget ────────────────────────────────────────────────────
class ChatbotPanel(QWidget):
    """
    Side-panel Groq chatbot.
    Call `update_context(code, filename, language)` whenever the active tab changes.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._api_key: str = ""
        self._history: list[dict] = []
        self._context_code: str = ""
        self._context_file: str = ""
        self._context_lang: str = ""
        self._busy: bool = False
        self._thread: QThread | None = None
        self._worker: _GroqWorker | None = None
        self._thinking_widget: _BubbleWidget | None = None

        self._build_ui()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_api_key(self, key: str) -> None:
        self._api_key = key.strip()

    def update_context(self, code: str, filename: str, language: str) -> None:
        self._context_code = code
        self._context_file = filename
        self._context_lang = language
        label = f"📄 {filename} ({language})" if filename else f"📄 {language or 'No file'}"
        self._ctx_label.setText(label)

    def clear_chat(self) -> None:
        self._history.clear()
        # Remove all bubble widgets
        while self._msg_layout.count():
            item = self._msg_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._append_bubble("system", "Conversation cleared. Context still active.")

    # ── UI builder ────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ──
        header = QFrame()
        header.setStyleSheet("background:#1e1e2e; border-bottom:1px solid #313244;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(10, 6, 10, 6)
        title = QLabel("🤖 AI Chatbot")
        title.setStyleSheet("color:#cba6f7; font-weight:bold; font-size:13px;")
        hl.addWidget(title)
        hl.addStretch()
        clear_btn = QPushButton("🗑 Clear")
        clear_btn.setFixedHeight(24)
        clear_btn.setStyleSheet(
            "QPushButton{background:#313244;color:#cdd6f4;border:none;"
            "border-radius:4px;padding:0 8px;font-size:11px;}"
            "QPushButton:hover{background:#45475a;}"
        )
        clear_btn.clicked.connect(self.clear_chat)
        hl.addWidget(clear_btn)
        layout.addWidget(header)

        # ── Context label ──
        self._ctx_label = QLabel("📄 No file open")
        self._ctx_label.setStyleSheet(
            "color:#6c7086; font-size:10px; padding:3px 10px;"
            "background:#181825; border-bottom:1px solid #313244;"
        )
        self._ctx_label.setWordWrap(True)
        layout.addWidget(self._ctx_label)

        # ── Scroll area for messages ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            "QScrollArea{background:#1e1e2e;border:none;}"
            "QScrollBar:vertical{background:#181825;width:6px;}"
            "QScrollBar::handle:vertical{background:#45475a;border-radius:3px;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px;}"
        )

        # Container inside scroll area
        self._msg_container = QWidget()
        self._msg_container.setStyleSheet("background:#1e1e2e;")
        self._msg_layout = QVBoxLayout(self._msg_container)
        self._msg_layout.setContentsMargins(8, 8, 8, 8)
        self._msg_layout.setSpacing(4)
        self._msg_layout.addStretch()    # pushes messages up from bottom initially

        self._scroll.setWidget(self._msg_container)
        layout.addWidget(self._scroll, stretch=1)

        # ── Input area ──
        input_frame = QFrame()
        input_frame.setStyleSheet("background:#181825; border-top:1px solid #313244;")
        inp_layout = QVBoxLayout(input_frame)
        inp_layout.setContentsMargins(8, 8, 8, 8)
        inp_layout.setSpacing(6)

        # Quick chips
        chips_row = QHBoxLayout()
        chips_row.setSpacing(4)
        for label, prompt in [
            ("💡 Explain", "Is code ko simple terms mein explain karo."),
            ("🐛 Debug",   "Is code mein koi bug hai? Dhundho aur batao."),
            ("⚡ Optimize", "Is code ko optimize kaise karein?"),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(22)
            btn.setStyleSheet(
                "QPushButton{background:#313244;color:#89b4fa;border:none;"
                "border-radius:3px;padding:0 6px;font-size:10px;}"
                "QPushButton:hover{background:#45475a;}"
            )
            btn.clicked.connect(lambda _=False, p=prompt: self._send_message(p))
            chips_row.addWidget(btn)
        chips_row.addStretch()
        inp_layout.addLayout(chips_row)

        # Input + send
        row = QHBoxLayout()
        row.setSpacing(6)
        self._input = QLineEdit()
        self._input.setPlaceholderText("Hindi ya English mein poochho...")
        self._input.setStyleSheet(
            "QLineEdit{background:#313244;color:#cdd6f4;"
            "border:1px solid #45475a;border-radius:6px;padding:6px 10px;font-size:12px;}"
            "QLineEdit:focus{border:1px solid #cba6f7;}"
        )
        self._input.returnPressed.connect(self._on_send)
        row.addWidget(self._input, stretch=1)

        self._send_btn = QPushButton("Send")
        self._send_btn.setFixedSize(60, 32)
        self._send_btn.setStyleSheet(
            "QPushButton{background:#cba6f7;color:#1e1e2e;border:none;"
            "border-radius:6px;font-weight:bold;font-size:12px;}"
            "QPushButton:hover{background:#d0bcff;}"
            "QPushButton:disabled{background:#45475a;color:#6c7086;}"
        )
        self._send_btn.clicked.connect(self._on_send)
        row.addWidget(self._send_btn)
        inp_layout.addLayout(row)
        layout.addWidget(input_frame)

        # Welcome message
        self._append_bubble(
            "assistant",
            "Namaste! 👋 Main tumhara AI assistant hoon.\n"
            "Jo tab abhi khula hai uska code main dekh sakta hoon.\n"
            "Kuch bhi poochho — explain, debug, optimize!",
        )

    # ── Messaging ─────────────────────────────────────────────────────────────

    def _on_send(self) -> None:
        text = self._input.text().strip()
        if not text or self._busy:
            return
        self._input.clear()
        self._send_message(text)

    def _send_message(self, user_text: str) -> None:
        if self._busy:
            return

        if not self._api_key:
            self._append_bubble(
                "error",
                "⚠️ Groq API key nahi mili.\nSettings → Preferences → Groq API Key daalo.",
            )
            return

        self._append_bubble("user", user_text)

        # Build context-aware system message
        context_parts = [_SYSTEM_PROMPT]
        if self._context_code.strip():
            lang  = self._context_lang or "text"
            fname = self._context_file or "current file"
            lines = self._context_code.splitlines()
            code_snippet = (
                "\n".join(lines[:200]) + f"\n... ({len(lines)-200} more lines)"
                if len(lines) > 200 else self._context_code
            )
            context_parts.append(
                f"\n\nCurrent open file: {fname} ({lang})\n"
                f"```{lang.lower()}\n{code_snippet}\n```"
            )
        else:
            context_parts.append("\n\nNo file is currently open in the editor.")

        messages = [{"role": "system", "content": "".join(context_parts)}]
        messages.extend(self._history[-20:])
        messages.append({"role": "user", "content": user_text})
        self._history.append({"role": "user", "content": user_text})

        self._set_busy(True)
        self._append_bubble("thinking", "")

        self._thread = QThread()
        self._worker = _GroqWorker(self._api_key, messages)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_reply)
        self._worker.errored.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.errored.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_reply(self, text: str) -> None:
        self._remove_thinking()
        self._history.append({"role": "assistant", "content": text})
        self._append_bubble("assistant", text)
        self._set_busy(False)

    def _on_error(self, msg: str) -> None:
        self._remove_thinking()
        self._append_bubble("error", msg)
        self._set_busy(False)

    # ── Bubble management ─────────────────────────────────────────────────────

    def _append_bubble(self, role: str, text: str) -> None:
        """Create a _BubbleWidget and insert it before the trailing stretch."""
        bubble = _BubbleWidget(role, text)
        if role == "thinking":
            self._thinking_widget = bubble

        # Insert before the last stretch item
        count = self._msg_layout.count()
        insert_pos = max(count - 1, 0)  # before the trailing stretch
        self._msg_layout.insertWidget(insert_pos, bubble)

        # Scroll to bottom after layout update
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _remove_thinking(self) -> None:
        if self._thinking_widget is not None:
            self._msg_layout.removeWidget(self._thinking_widget)
            self._thinking_widget.deleteLater()
            self._thinking_widget = None

    def _scroll_to_bottom(self) -> None:
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._send_btn.setEnabled(not busy)
        self._input.setEnabled(not busy)
        self._send_btn.setText("..." if busy else "Send")
