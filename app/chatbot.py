"""
ncode — Live Groq Chatbot Panel
A side-panel chatbot that is always aware of the currently open tab's code,
filename, and language. The user can ask questions in Hindi or English.
Uses the same urllib-only Groq pattern as the rest of the project.
"""
from __future__ import annotations

import json
import re
import threading
import urllib.error
import urllib.request
from typing import Callable

from PySide6.QtCore import Qt, Signal as Sig, QObject, QThread
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QFrame,
    QSizePolicy,
)

# ── Groq config (same as rest of app) ────────────────────────────────────────
_GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL = "llama-3.3-70b-versatile"

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
    finished   = Sig(str)   # reply text
    errored    = Sig(str)   # error message

    def __init__(
        self,
        api_key: str,
        messages: list[dict],
    ) -> None:
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
                _GROQ_URL,
                data=data,
                headers={
                    "Content-Type": "application/json",
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
            else:
                self.errored.emit(f"❌ Groq HTTP {e.code} error.")
        except urllib.error.URLError:
            self.errored.emit("❌ Network error — internet check karo.")
        except Exception as e:  # noqa: BLE001
            self.errored.emit(f"❌ Error: {e}")


# ── Main Chat Panel widget ────────────────────────────────────────────────────
class ChatbotPanel(QWidget):
    """
    Side-panel Groq chatbot.
    Call `update_context(code, filename, language)` whenever the active tab changes.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._api_key: str = ""
        self._history: list[dict] = []          # OpenAI-style message list
        self._context_code: str = ""
        self._context_file: str = ""
        self._context_lang: str = ""
        self._busy: bool = False
        self._thread: QThread | None = None
        self._worker: _GroqWorker | None = None

        self._build_ui()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_api_key(self, key: str) -> None:
        self._api_key = key.strip()

    def update_context(self, code: str, filename: str, language: str) -> None:
        """Call this whenever the active editor tab changes."""
        self._context_code = code
        self._context_file = filename
        self._context_lang = language
        # Update context label
        label = f"📄 {filename} ({language})" if filename else f"📄 {language or 'No file'}"
        self._ctx_label.setText(label)

    def clear_chat(self) -> None:
        self._history.clear()
        self._chat_display.clear()
        self._append_bubble("system", "🤖 Conversation cleared. Context still active.")

    # ── UI builder ────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ──
        header = QFrame()
        header.setStyleSheet("background:#1e1e2e; border-bottom:1px solid #313244;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)

        title = QLabel("🤖 AI Chatbot")
        title.setStyleSheet("color:#cba6f7; font-weight:bold; font-size:13px;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        clear_btn = QPushButton("🗑 Clear")
        clear_btn.setFixedHeight(24)
        clear_btn.setStyleSheet(
            "QPushButton{background:#313244;color:#cdd6f4;border:none;border-radius:4px;padding:0 8px;font-size:11px;}"
            "QPushButton:hover{background:#45475a;}"
        )
        clear_btn.clicked.connect(self.clear_chat)
        header_layout.addWidget(clear_btn)

        layout.addWidget(header)

        # ── Context label ──
        self._ctx_label = QLabel("📄 No file open")
        self._ctx_label.setStyleSheet(
            "color:#6c7086; font-size:10px; padding:3px 10px;"
            "background:#181825; border-bottom:1px solid #313244;"
        )
        self._ctx_label.setWordWrap(True)
        layout.addWidget(self._ctx_label)

        # ── Chat display ──
        self._chat_display = QTextEdit()
        self._chat_display.setReadOnly(True)
        self._chat_display.setStyleSheet(
            "QTextEdit{"
            "  background:#1e1e2e; color:#cdd6f4;"
            "  border:none; font-family:monospace; font-size:12px;"
            "  padding:8px;"
            "}"
        )
        self._chat_display.setWordWrapMode(True)  # type: ignore[arg-type]
        layout.addWidget(self._chat_display, stretch=1)

        # ── Input area ──
        input_frame = QFrame()
        input_frame.setStyleSheet("background:#181825; border-top:1px solid #313244;")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(6)

        # Quick action chips
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(4)
        for label, prompt in [
            ("💡 Explain", "Is code ko explain karo in simple terms."),
            ("🐛 Debug",   "Is code mein koi bug hai? Dhundho."),
            ("⚡ Optimize","Is code ko optimize kaise karte hain?"),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(22)
            btn.setStyleSheet(
                "QPushButton{background:#313244;color:#89b4fa;border:none;border-radius:3px;"
                "padding:0 6px;font-size:10px;}"
                "QPushButton:hover{background:#45475a;}"
            )
            btn.clicked.connect(lambda checked=False, p=prompt: self._send_message(p))
            chips_layout.addWidget(btn)
        chips_layout.addStretch()
        input_layout.addLayout(chips_layout)

        # Text input + send button
        row = QHBoxLayout()
        row.setSpacing(6)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Hindi ya English mein poochho...")
        self._input.setStyleSheet(
            "QLineEdit{"
            "  background:#313244; color:#cdd6f4; border:1px solid #45475a;"
            "  border-radius:6px; padding:6px 10px; font-size:12px;"
            "}"
            "QLineEdit:focus{border:1px solid #cba6f7;}"
        )
        self._input.returnPressed.connect(self._on_send)
        row.addWidget(self._input, stretch=1)

        self._send_btn = QPushButton("Send")
        self._send_btn.setFixedSize(60, 32)
        self._send_btn.setStyleSheet(
            "QPushButton{background:#cba6f7;color:#1e1e2e;border:none;border-radius:6px;"
            "font-weight:bold;font-size:12px;}"
            "QPushButton:hover{background:#d0bcff;}"
            "QPushButton:disabled{background:#45475a;color:#6c7086;}"
        )
        self._send_btn.clicked.connect(self._on_send)
        row.addWidget(self._send_btn)

        input_layout.addLayout(row)
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

        # Build context-aware system message for this turn
        context_parts = [_SYSTEM_PROMPT]
        if self._context_code.strip():
            lang = self._context_lang or "text"
            fname = self._context_file or "current file"
            # Only send first 200 lines of code to stay within token limits
            lines = self._context_code.splitlines()
            if len(lines) > 200:
                code_snippet = "\n".join(lines[:200]) + f"\n... ({len(lines)-200} more lines)"
            else:
                code_snippet = self._context_code
            context_parts.append(
                f"\n\nCurrent open file: {fname} ({lang})\n"
                f"```{lang.lower()}\n{code_snippet}\n```"
            )
        else:
            context_parts.append("\n\nNo file is currently open in the editor.")

        system_content = "".join(context_parts)

        messages = [{"role": "system", "content": system_content}]
        # Add conversation history (last 10 turns to avoid token overflow)
        messages.extend(self._history[-20:])
        messages.append({"role": "user", "content": user_text})

        # Save to history
        self._history.append({"role": "user", "content": user_text})

        self._set_busy(True)
        self._append_bubble("thinking", "⏳ Thinking...")

        # Spin up QThread
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

    # ── Display helpers ───────────────────────────────────────────────────────

    def _append_bubble(self, role: str, text: str) -> None:
        """Append a styled chat bubble to the display."""
        colors = {
            "user":      ("#89dceb", "#1e3a4a", "You"),
            "assistant": ("#a6e3a1", "#1e3a2a", "AI"),
            "error":     ("#f38ba8", "#3a1e2a", "⚠"),
            "system":    ("#6c7086", "#1e1e2e", ""),
            "thinking":  ("#fab387", "#1e1e2e", "AI"),
        }
        color, bg, label = colors.get(role, ("#cdd6f4", "#1e1e2e", ""))

        # Escape HTML
        safe = (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )

        # Render code blocks
        safe = re.sub(
            r"```(\w*)\n?(.*?)```",
            lambda m: (
                f'<pre style="background:#11111b;color:#89b4fa;padding:6px;'
                f'border-radius:4px;margin:4px 0;font-size:11px;">'
                f'{m.group(2)}</pre>'
            ),
            safe,
            flags=re.DOTALL,
        )

        # Inline code
        safe = re.sub(
            r"`([^`]+)`",
            r'<code style="background:#313244;color:#f38ba8;padding:1px 4px;border-radius:3px;">\1</code>',
            safe,
        )

        # Newlines
        safe = safe.replace("\n", "<br>")

        if label:
            header_html = (
                f'<span style="color:{color};font-weight:bold;font-size:11px;">{label}</span><br>'
            )
        else:
            header_html = ""

        bubble_html = (
            f'<div style="margin:6px 2px;padding:8px 10px;'
            f'background:{bg};border-radius:8px;'
            f'border-left:3px solid {color};">'
            f'{header_html}'
            f'<span style="color:#cdd6f4;font-size:12px;">{safe}</span>'
            f'</div>'
        )

        cursor = self._chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._chat_display.setTextCursor(cursor)
        self._chat_display.insertHtml(bubble_html + "<br>")
        self._chat_display.verticalScrollBar().setValue(
            self._chat_display.verticalScrollBar().maximum()
        )

    def _remove_thinking(self) -> None:
        """Remove the last 'Thinking...' bubble (simple approach: remove last inserted block)."""
        doc = self._chat_display.document()
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.MoveOperation.End)
        # Find and remove the thinking block from display — we re-render everything simply
        # Instead: just leave thinking text and overwrite by removing last N chars approach.
        # Simple approach: store position before thinking bubble and restore.
        # We use a flag-based approach with HTML — for simplicity just append [done] note
        # Actually: scroll up and remove last block
        html = self._chat_display.toHtml()
        # Remove the thinking bubble div (last occurrence)
        # Pattern: the ⏳ Thinking... bubble
        cleaned = re.sub(
            r'<div[^>]*>.*?⏳.*?Thinking.*?</div>\s*(<br>)?',
            '',
            html,
            count=1,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if cleaned != html:
            self._chat_display.setHtml(cleaned)
            self._chat_display.verticalScrollBar().setValue(
                self._chat_display.verticalScrollBar().maximum()
            )

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._send_btn.setEnabled(not busy)
        self._input.setEnabled(not busy)
        self._send_btn.setText("..." if busy else "Send")
