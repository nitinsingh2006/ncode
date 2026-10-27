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
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

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

_SYSTEM_PROMPT = """You are the AI engine of **ncode** (Nitin Editor) — a desktop code editor built with Python + PySide6.
You are deeply integrated into ncode. You know everything about it and can help the user use, control, and extend it.

== WHO YOU ARE ==
- You are Groq AI (model: qwen/qwen3.8-27b), embedded as a live side-panel chatbot inside ncode.
- You always see the code in the currently open editor tab as context.
- You reply in the same language the user uses: Hindi, English, or Hinglish.
- Keep answers concise and practical. Format code with triple backticks.
- Do NOT output the user's full code back unless explicitly asked.

== NCODE: FULL KNOWLEDGE ==

**What is ncode?**
ncode is a fully local desktop code editor for Linux (Ubuntu), made by Nitin Singh.
GitHub: https://github.com/nitinsingh2006/ncode

**Tech Stack:** Python 3.10+, PySide6 (Qt6), SQLite, Groq API (you), stdlib urllib.

**Features:**
1. Multi-tab code editor with syntax highlighting (Pygments) for 18+ languages
2. Code runner: Ctrl+Enter / F5 — runs Python, C, C++, Java, JS, TS, Go, Rust, Ruby, Kotlin, PHP, Bash, SQL, HTML/CSS, and more
3. Integrated terminal (real bash shell)
4. SQL executor — runs SQLite queries locally, no server needed
5. HTML/CSS runner — opens in default browser, live preview panel
6. AI Code Transpiler — converts code from one language to another (uses Groq/you)
7. DSA Practice — 187 problems (Striver SDE + NeetCode 150), 21 topics, AI solution checker
8. Live AI Chatbot — that's you! Side panel, context-aware, Hindi/English/Hinglish
9. Find & Replace, zoom, word wrap, auto-indent, bracket matching

**Keyboard Shortcuts:**
- Ctrl+Enter / F5 → Run code
- Ctrl+Shift+C → Stop execution
- Ctrl+N → New tab
- Ctrl+O → Open file
- Ctrl+S → Save
- Ctrl+H → Find & Replace
- Ctrl+, → Settings/Preferences
- Ctrl+Shift+D → Toggle DSA sidebar
- Ctrl+Shift+G → Check DSA solution with AI
- Ctrl+Shift+T → AI code transpiler
- Ctrl+Shift+I → Toggle this AI Chatbot
- Ctrl+Shift+P → HTML preview

**UI Layout:**
- Left sidebar: DSA Practice panel (toggle with Ctrl+Shift+D)
- Center: multi-tab code editor
- Bottom panels: PROBLEMS | OUTPUT | TERMINAL | DSA FEEDBACK
- Right sidebar: this AI Chatbot (toggle with Ctrl+Shift+I)
- Toolbar: New, Open, Save | Language selector | RUN | STOP | 💬 Chat | ⚙ Settings

**Important Files (for developers):**
- app/main.py — main window (NitinEditor class), 3000+ lines
- app/editor.py — CodeEditor with syntax highlighting
- app/compiler.py — language configs, build commands
- app/chatbot.py — this file! You live here.
- app/dsa/ — DSA practice module (bank.py, checker.py, panel.py, starters.py, storage.py)
- app/ai_transpiler.py — language transpiler
- app/settings.py — user settings (~/.config/nitin-editor/settings.json)
- tests/ — 74 pytest tests, all passing

**DSA Practice:**
- 187 questions, 21 topics: Arrays, Trees, Graphs, DP, Binary Search, Linked List, Stack, etc.
- Striver SDE Sheet (139 q) + NeetCode 150 (159 q), "Both" means counted in both
- Questions have: problem statement, examples, constraints, time/space complexity
- Starter code generated for 11 languages
- AI checker (Ctrl+Shift+G): gives verdict (correct/incorrect), issues, edge cases, complexity, hint
- Solutions saved to: ~/.local/share/nitin-editor/solutions.db

**Settings & API Key:**
- Settings file: ~/.config/nitin-editor/settings.json
- Keys: theme, font_size, tab_size, word_wrap, groq_api_key, recent_files
- Groq API key is required for: chatbot (you), DSA checker, AI transpiler
- Free key at: https://console.groq.com

**Code Block Buttons (in this chatbot):**
- ⧉ Copy — copies code to clipboard
- → Editor — inserts code directly into the current open editor tab
- ▶ Run Code — inserts code into editor AND runs it immediately with 1 click
- ⚡ Run in Terminal — runs terminal commands in ncode's integrated terminal with 1 click

CRITICAL FORMATTING RULES:
1. When providing code, ALWAYS wrap it in complete standard ```language ... ``` code blocks.
2. When suggesting ANY command (like `pip install pygame`, `sudo apt install ...`, git, etc.), ALWAYS put it inside its own ```bash ... ``` code block! Do NOT write install commands in plain prose without code blocks. This enables the user to click '⚡ Run in Terminal' to run it automatically!

== YOUR CAPABILITIES ==
When the user asks you to:
- **Explain code** → analyze the code in context and explain it clearly
- **Debug code** → find bugs, suggest fixes with corrected code
- **Optimize code** → suggest better time/space complexity approaches
- **Write code** → write complete solutions; user can use → Editor button to paste
- **Help with DSA** → explain algorithms, suggest approach, hint (not full solution unless asked)
- **Help with ncode** → explain features, shortcuts, how to use any part of ncode
- **Convert language** → suggest using Ctrl+Shift+T (AI Transpiler) or write the conversion yourself
- **Fix errors** → look at error message + code in context and provide the fix

You are not just a chatbot — you are the AI brain of ncode. Act accordingly.
"""


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
                "max_tokens": 4096,
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


# ── Code Block Widget (with copy, insert, and terminal runner) ───────────────
class _CodeBlockWidget(QWidget):
    """
    Renders a single fenced code block with:
    - Language tag + action buttons in header bar:
      - '⚡ Run in Terminal' for bash/pip/shell commands
      - '→ Editor' to paste into the active tab
      - '▶ Run Code' to paste AND immediately run in editor
      - '⧉ Copy' to copy to clipboard
    - A read-only QPlainTextEdit showing the code
    """

    def __init__(
        self,
        code: str,
        lang: str = "",
        on_insert=None,          # callable(code: str, lang: str) | None
        on_run=None,             # callable(code: str, lang: str) | None
        on_terminal=None,        # callable(cmd: str) | None
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._code = code
        self._lang = lang
        self._on_insert = on_insert
        self._on_run = on_run
        self._on_terminal = on_terminal
        self._copied_timer: QTimer | None = None
        self._build(lang)

    def _build(self, lang: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header bar ──
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background:#181825; border-radius:6px 6px 0 0; border-bottom:1px solid #313244; }"
        )
        hlay = QHBoxLayout(header)
        hlay.setContentsMargins(10, 6, 8, 6)
        hlay.setSpacing(6)

        lang_lbl = QLabel(lang.lower() if lang else "code")
        lang_lbl.setStyleSheet("color:#a6adc8; font-size:11px; font-family:monospace; font-weight:bold;")
        hlay.addWidget(lang_lbl)
        hlay.addStretch()

        # Detect if this block is terminal commands
        is_cmd = (
            lang.lower() in ("bash", "sh", "shell", "terminal", "zsh", "cmd")
            or any(
                line.strip().startswith(("pip ", "pip3 ", "sudo ", "npm ", "cargo ", "git ", "apt ", "python3 -m pip "))
                for line in self._code.splitlines() if line.strip() and not line.strip().startswith("#")
            )
        )

        if is_cmd:
            if self._on_terminal is not None:
                self._term_btn = QPushButton("⚡ Run in Terminal")
                self._term_btn.setFixedHeight(24)
                self._term_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                self._term_btn.setToolTip("Click to execute this command in ncode's integrated terminal automatically")
                self._term_btn.setStyleSheet(
                    "QPushButton {"
                    "  background:#fab387; color:#11111b; border:none; border-radius:4px;"
                    "  padding: 0 10px; font-size:11px; font-weight:bold;"
                    "}"
                    "QPushButton:hover { background:#f9c09b; }"
                )
                self._term_btn.clicked.connect(self._run_terminal_cmd)
                hlay.addWidget(self._term_btn)
        else:
            # Code block: provide → Editor and ▶ Run Code buttons
            if self._on_insert is not None:
                self._insert_btn = QPushButton("→ Editor")
                self._insert_btn.setFixedHeight(24)
                self._insert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                self._insert_btn.setToolTip("Insert this code into the active editor tab")
                self._insert_btn.setStyleSheet(
                    "QPushButton {"
                    "  background:#a6e3a1; color:#11111b; border:none; border-radius:4px;"
                    "  padding: 0 10px; font-size:11px; font-weight:bold;"
                    "}"
                    "QPushButton:hover { background:#b5e8b1; }"
                )
                self._insert_btn.clicked.connect(self._insert_to_editor)
                hlay.addWidget(self._insert_btn)

            if self._on_run is not None:
                self._run_btn = QPushButton("▶ Run Code")
                self._run_btn.setFixedHeight(24)
                self._run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                self._run_btn.setToolTip("Insert into editor AND run immediately")
                self._run_btn.setStyleSheet(
                    "QPushButton {"
                    "  background:#89b4fa; color:#11111b; border:none; border-radius:4px;"
                    "  padding: 0 10px; font-size:11px; font-weight:bold;"
                    "}"
                    "QPushButton:hover { background:#99c1fc; }"
                )
                self._run_btn.clicked.connect(self._insert_and_run)
                hlay.addWidget(self._run_btn)

        # Copy button
        self._copy_btn = QPushButton("⧉ Copy")
        self._copy_btn.setFixedHeight(24)
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.setStyleSheet(
            "QPushButton {"
            "  background:#313244; color:#cdd6f4; border:1px solid #45475a; border-radius:4px;"
            "  padding: 0 10px; font-size:11px; font-weight:bold;"
            "}"
            "QPushButton:hover { background:#45475a; }"
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
        lines = self._code.count("\n") + 1
        line_h = code_edit.fontMetrics().height()
        target_h = min(lines * line_h + 24, 300)
        code_edit.setFixedHeight(target_h)
        layout.addWidget(code_edit)

    def _run_terminal_cmd(self) -> None:
        if self._on_terminal:
            self._on_terminal(self._code)
            if hasattr(self, "_term_btn"):
                self._term_btn.setText("✓ Running...")
                QTimer.singleShot(2000, lambda: self._term_btn.setText("⚡ Run in Terminal") if hasattr(self, "_term_btn") else None)

    def _insert_to_editor(self) -> None:
        if self._on_insert:
            self._on_insert(self._code, self._lang)
            if hasattr(self, "_insert_btn"):
                self._insert_btn.setText("✓ Inserted!")
                QTimer.singleShot(2000, lambda: self._insert_btn.setText("→ Editor") if hasattr(self, "_insert_btn") else None)

    def _insert_and_run(self) -> None:
        if self._on_run:
            self._on_run(self._code, self._lang)
            if hasattr(self, "_run_btn"):
                self._run_btn.setText("✓ Running...")
                QTimer.singleShot(2000, lambda: self._run_btn.setText("▶ Run Code") if hasattr(self, "_run_btn") else None)

    def _copy_code(self) -> None:
        QGuiApplication.clipboard().setText(self._code)
        self._copy_btn.setText("✓ Copied!")
        self._copy_btn.setStyleSheet(
            "QPushButton {"
            "  background:#a6e3a1; color:#1e1e2e;"
            "  border:none; border-radius:4px;"
            "  padding: 0 10px; font-size:11px; font-weight:bold;"
            "}"
        )
        if self._copied_timer:
            self._copied_timer.stop()
        self._copied_timer = QTimer()
        self._copied_timer.setSingleShot(True)
        self._copied_timer.timeout.connect(self._reset_copy_btn)
        self._copied_timer.start(2000)

    def _reset_copy_btn(self) -> None:
        self._copy_btn.setText("⧉ Copy")
        self._copy_btn.setStyleSheet(
            "QPushButton {"
            "  background:#313244; color:#cdd6f4; border:1px solid #45475a; border-radius:4px;"
            "  padding: 0 10px; font-size:11px; font-weight:bold;"
            "}"
            "QPushButton:hover { background:#45475a; }"
        )


# ── Single message bubble widget ──────────────────────────────────────────────
class _BubbleWidget(QWidget):
    """
    One chat message. Parses text + fenced code blocks and renders them
    as a mix of QLabel (text) and _CodeBlockWidget (code blocks).
    """

    def __init__(
        self,
        role: str,
        text: str,
        on_insert=None,
        on_run=None,
        on_terminal=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._role = role
        self._on_insert = on_insert
        self._on_run = on_run
        self._on_terminal = on_terminal
        self._build(text)

    def _build(self, text: str) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 2, 0, 2)
        outer.setSpacing(0)

        if self._role == "user":
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
            segments = self._parse_segments(text)
            for kind, content, lang in segments:
                if kind == "code":
                    cb = _CodeBlockWidget(
                        content,
                        lang,
                        on_insert=self._on_insert,
                        on_run=self._on_run,
                        on_terminal=self._on_terminal,
                    )
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
        """
        Split text into alternating ('text', ..., '') and ('code', ..., lang) segments.
        Handles:
        - Closed ```lang\ncode``` or '''lang\ncode'''
        - Unclosed / truncated ```lang\ncode (when token limit reached before closing)
        """
        pattern = re.compile(r"(?:`{3}|\x27{3})(\w*)\n?(.*?)(?:`{3}|\x27{3})", re.DOTALL)
        segments: list[tuple[str, str, str]] = []
        last = 0
        for m in pattern.finditer(text):
            if m.start() > last:
                segments.append(("text", text[last:m.start()], ""))
            lang = m.group(1).strip()
            code = m.group(2)
            segments.append(("code", code, lang))
            last = m.end()

        # Check for unclosed fence at the end of the text (e.g. if response was truncated)
        rem = text[last:]
        m_unclosed = re.search(r"(?:`{3}|\x27{3})(\w*)\n?(.*)", rem, re.DOTALL)
        if m_unclosed and m_unclosed.group(2).strip():
            pre = rem[:m_unclosed.start()]
            if pre.strip():
                segments.append(("text", pre, ""))
            lang = m_unclosed.group(1).strip()
            code = m_unclosed.group(2)
            segments.append(("code", code, lang))
        elif rem:
            segments.append(("text", rem, ""))
        return segments

    @staticmethod
    def _escape(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @staticmethod
    def _render_inline(s: str) -> str:
        s = re.sub(
            r"`([^`]+)`",
            r'<code style="background:#313244;color:#f38ba8;padding:1px 5px;'
            r'border-radius:3px;font-size:11px;">\1</code>',
            s,
        )
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        return s


# ── Main Chat Panel widget ────────────────────────────────────────────────────
class ChatbotPanel(QWidget):
    """
    Side-panel Groq chatbot.
    Call `update_context(code, filename, language)` whenever the active tab changes.
    Signals:
    - insert_to_editor(code, lang): insert into editor tab
    - insert_and_run(code, lang): insert and trigger run
    - run_in_terminal(cmd): execute command in terminal
    """

    insert_to_editor = Sig(str, str)
    insert_and_run   = Sig(str, str)
    run_in_terminal  = Sig(str)

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

        # Admin mode: lets Groq edit ncode codebase files
        self._admin_mode: bool = False
        self._ncode_root: Path = Path(__file__).resolve().parent.parent

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

        # Admin mode toggle button
        self._admin_btn = QPushButton("🔧 Admin")
        self._admin_btn.setFixedHeight(24)
        self._admin_btn.setCheckable(True)
        self._admin_btn.setToolTip(
            "Admin Mode: Groq can read & edit ncode codebase files.\n"
            "Always shows a confirmation dialog before any file is changed."
        )
        self._admin_btn.setStyleSheet(
            "QPushButton{background:#313244;color:#fab387;border:1px solid #45475a;"
            "border-radius:4px;padding:0 8px;font-size:11px;}"
            "QPushButton:hover{background:#45475a;}"
            "QPushButton:checked{background:#fab387;color:#1e1e2e;border:none;font-weight:bold;}"
        )
        self._admin_btn.clicked.connect(self._toggle_admin)
        hl.addWidget(self._admin_btn)

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

    def _toggle_admin(self) -> None:
        self._admin_mode = self._admin_btn.isChecked()
        if self._admin_mode:
            self._append_bubble(
                "system",
                "🔧 Admin Mode ON — Groq ab ncode ke files padh aur edit kar sakta hai.\n"
                "Har edit se pehle confirmation dialog aayega.",
            )
        else:
            self._append_bubble("system", "🔧 Admin Mode OFF.")

    def _build_dsa_context(self) -> str:
        """Load DSA solved/pending questions from DB and return summary string."""
        try:
            from app.dsa.bank import get_all_questions
            from app.dsa.storage import get_solved_ids, get_topic_progress, get_sheet_progress
            questions = get_all_questions()
            solved_ids = get_solved_ids()
            solved_qs  = [q for q in questions if q.id in solved_ids]
            pending_qs = [q for q in questions if q.id not in solved_ids]
            sheet_prog = get_sheet_progress(questions)
            topic_prog = get_topic_progress(questions)

            lines = [
                f"\n\n== DSA PROGRESS (live data from user's DB) ==",
                f"Total questions: {len(questions)} | Solved: {len(solved_qs)} | Pending: {len(pending_qs)}",
                f"Striver SDE: {sheet_prog['Striver'][0]}/{sheet_prog['Striver'][1]} solved",
                f"NeetCode 150: {sheet_prog['NeetCode'][0]}/{sheet_prog['NeetCode'][1]} solved",
                "\nPer-topic progress:",
            ]
            for topic, (s, t) in sorted(topic_prog.items()):
                lines.append(f"  {topic}: {s}/{t} solved")

            if solved_qs:
                lines.append("\nRecently solved (last 10):")
                # Get solved with timestamps from storage
                try:
                    from app.dsa.storage import get_solution
                    solved_with_time = []
                    for q in solved_qs:
                        sol = get_solution(q.id)
                        if sol:
                            solved_with_time.append((q, sol.saved_at))
                    solved_with_time.sort(key=lambda x: x[1], reverse=True)
                    for q, ts in solved_with_time[:10]:
                        lines.append(f"  ✅ [{q.topic}] {q.title} ({q.difficulty}) — {ts[:10]}")
                except Exception:
                    for q in solved_qs[-10:]:
                        lines.append(f"  ✅ [{q.topic}] {q.title} ({q.difficulty})")

            if pending_qs:
                lines.append(f"\nPending questions (first 20 of {len(pending_qs)}):")
                for q in pending_qs[:20]:
                    lines.append(f"  ⬜ [{q.topic}] {q.title} ({q.difficulty}, {q.source})")

            return "\n".join(lines)
        except Exception as e:
            return f"\n\n[DSA data unavailable: {e}]"

    def _build_admin_context(self) -> str:
        """Build ncode file tree for admin mode context."""
        try:
            root = self._ncode_root
            files = []
            for p in sorted(root.rglob("*.py")):
                rel = p.relative_to(root)
                parts = rel.parts
                if any(x in parts for x in (".venv", "__pycache__", ".git")):
                    continue
                files.append(str(rel))
            tree = "\n  ".join(files[:60])
            return (
                f"\n\n== ADMIN MODE: ncode CODEBASE ==\n"
                f"Root: {root}\n"
                f"Key Python files:\n  {tree}\n\n"
                "To edit a file, respond with a block in this EXACT format (nothing before/after):\n"
                "```edit:relative/path/to/file.py\n<complete new file content here>\n```\n"
                "IMPORTANT: Output the ENTIRE file content, not just the changed part.\n"
                "Always explain what you changed and why, BEFORE the edit block.\n"
                "The user will see a confirmation dialog before any file is saved."
            )
        except Exception as e:
            return f"\n\n[Admin context error: {e}]"

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


        # Inject live DSA progress from user's DB
        context_parts.append(self._build_dsa_context())

        # Admin mode: inject codebase map + file edit instructions
        if self._admin_mode:
            context_parts.append(self._build_admin_context())
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
        # In admin mode, check if Groq wants to edit a file
        if self._admin_mode:
            self._process_admin_edits(text)

    def _process_admin_edits(self, text: str) -> None:
        """Parse Groq response for ```edit:path``` blocks and apply with confirmation."""
        from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QPlainTextEdit as _PTE
        pattern = re.compile(r"```edit:([^\n]+)\n(.*?)```", re.DOTALL)
        for m in pattern.finditer(text):
            rel_path = m.group(1).strip()
            new_content = m.group(2)
            full_path = self._ncode_root / rel_path

            # Confirm dialog
            dlg = QMessageBox()
            dlg.setWindowTitle("🔧 Admin: File Edit Confirmation")
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.setText(
                f"<b>Groq wants to edit:</b><br><code>{rel_path}</code><br><br>"
                f"Preview (first 20 lines):<br>"
                f"<pre style='font-size:10px'>{chr(10).join(new_content.splitlines()[:20])}</pre>"
            )
            dlg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            dlg.button(QMessageBox.StandardButton.Yes).setText("✅ Apply Edit")
            dlg.button(QMessageBox.StandardButton.No).setText("❌ Skip")
            dlg.setStyleSheet(
                "QMessageBox{background:#1e1e2e;color:#cdd6f4;}"
                "QLabel{color:#cdd6f4;}"
            )
            result = dlg.exec()
            if result == QMessageBox.StandardButton.Yes:
                try:
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(new_content, encoding="utf-8")
                    self._append_bubble(
                        "system",
                        f"✅ File saved: `{rel_path}`\nRestart ncode to see changes take effect.",
                    )
                except Exception as e:
                    self._append_bubble("error", f"❌ Could not save `{rel_path}`: {e}")
            else:
                self._append_bubble("system", f"⏭ Skipped edit for `{rel_path}`")

    def _on_error(self, msg: str) -> None:
        self._remove_thinking()
        self._append_bubble("error", msg)
        self._set_busy(False)

    # ── Bubble management ─────────────────────────────────────────────────────

    def _append_bubble(self, role: str, text: str) -> None:
        """Create a _BubbleWidget and insert it before the trailing stretch."""
        bubble = _BubbleWidget(
            role,
            text,
            on_insert=self.insert_to_editor.emit,
            on_run=self.insert_and_run.emit,
            on_terminal=self.run_in_terminal.emit,
        )
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
