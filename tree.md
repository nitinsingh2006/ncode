# ncode — Project Map (`tree.md`)

> **Purpose:** Single-file reference for any developer or AI to instantly understand what ncode is, how it is structured, and where every feature lives. Read this before touching any code.

---

## What is ncode?

**ncode** (a.k.a. *Nitin Editor*) is a **desktop code editor** built with **Python + PySide6 (Qt6)**. It runs natively on Linux.

### Core capabilities (in one glance)

| Feature | Shortcut | Where |
|---|---|---|
| Multi-tab code editor with syntax highlighting | — | `app/editor.py` |
| Run code (18+ languages) | `Ctrl+Enter` / `F5` | `app/compiler.py`, `app/runner.py` |
| Integrated terminal | `Ctrl+`` | `app/terminal/` |
| SQL executor (SQLite, no server) | — | `app/sql/` |
| HTML/CSS live preview + browser open | `Ctrl+Shift+P` | `app/preview.py`, `app/compiler.py` |
| AI code transpiler (language→language) | `Ctrl+Shift+T` | `app/ai_transpiler.py` |
| **DSA Practice** — 187 questions, AI check | `Ctrl+Shift+G` | `app/dsa/` |
| **Live AI Chatbot** (Groq, context-aware) | `Ctrl+Shift+I` | `app/chatbot.py` |
| Settings / preferences | `Ctrl+,` | `app/settings.py`, `app/ui/` |

---

## How to Run

```bash
# Option 1 — launcher script (recommended)
./run.sh

# Option 2 — direct
source .venv/bin/activate
python3 -m app.main

# Option 3 — open a file directly
./run.sh path/to/file.py
```

**Only dependency:** `PySide6 >= 6.6.0` (see `requirements.txt`). Everything else is Python stdlib.

**Groq API key** → stored in `~/.config/nitin-editor/settings.json` under `groq_api_key`.  
Working model on this account: `qwen/qwen3.8-27b`.

---

## File Tree (annotated)

```
ncode/
│
├── install.sh              # 1-line curl installer: clones repo, runs setup, creates desktop icon
├── run.sh                  # Launcher: auto-detects first run, activates venv, runs app
├── setup.sh                # Setup: venv, PySide6, compilers, desktop icon, 'ncode' CLI
├── requirements.txt        # PySide6>=6.6.0  (only pip dep)
├── plan.md                 # Original 12-task dev plan (all done ✅)
├── tree.md                 # ← THIS FILE
│
├── assets/
│   ├── icon.png            # App icon (desktop + window)
│   └── icon.svg            # Source SVG
│
├── app/                    # All application source code
│   ├── __init__.py
│   │
│   ├── main.py             # ★ ENTRY POINT (3043 lines)
│   │                       #   NitinEditor(QMainWindow) — master class
│   │                       #   Builds entire UI, connects all signals
│   │                       #   Key methods:
│   │                       #     _build_toolbar()      — top toolbar + buttons
│   │                       #     _build_central()      — splitter layout
│   │                       #     _build_menu()         — menubar
│   │                       #     _new_tab()            — open new editor tab
│   │                       #     _run_code()           — trigger code execution
│   │                       #     _dsa_check_solution() — Groq DSA check
│   │                       #     _chatbot_toggle()     — show/hide chatbot
│   │                       #     _apply_settings()     — push settings to all widgets
│   │                       #     _on_tab_changed()     — sync chatbot context on tab switch
│   │
│   ├── editor.py           # CodeEditor(QPlainTextEdit) — 1064 lines
│   │                       #   Syntax highlighting (Pygments), line numbers,
│   │                       #   auto-indent, bracket matching, zoom, font size
│   │
│   ├── compiler.py         # Language configs + code compilation — 713 lines
│   │                       #   LANGUAGES dict: 18+ languages
│   │                       #   compile_code(): builds subprocess command
│   │                       #   HTML/CSS: writes temp file, opens in browser
│   │
│   ├── runner.py           # RunnerThread(QThread) — subprocess manager
│   │                       #   Runs compiled code, emits output/error signals
│   │                       #   Supports stdin, timeout, stop
│   │
│   ├── diagnostics.py      # Parse compiler errors → Problem panel items
│   │
│   ├── settings.py         # load_settings() / save_settings()
│   │                       #   Config file: ~/.config/nitin-editor/settings.json
│   │                       #   Keys: theme, font_size, tab_size, word_wrap,
│   │                       #         groq_api_key, gemini_api_key, recent_files
│   │
│   ├── preview.py          # HTML/CSS preview panel (uses QWebEngineView if available)
│   │
│   ├── terminal.py         # Legacy terminal shim (kept for compat)
│   │
│   ├── ai_transpiler.py    # Groq-powered code language transpiler
│   │                       #   transpile_async(): sends code + langs to Groq
│   │                       #   Model: qwen/qwen3.8-27b
│   │
│   ├── chatbot.py          # ★ Live AI Chatbot panel (Groq qwen/qwen3.8-27b)
│   │                       #   ChatbotPanel(QWidget) — right-side panel
│   │                       #   Always sees current tab's code (context-aware)
│   │                       #   User msgs: right-aligned purple (ChatGPT style)
│   │                       #   AI msgs: left-aligned green accent (Claude style)
│   │                       #   Code blocks with '⧉ Copy' + '→ Editor' buttons
│   │                       #   Live DSA querying (solved, pending, timestamps)
│   │                       #   🔧 Admin Mode: edit codebase files with confirmation dlg
│   │                       #   Quick chips: Explain / Debug / Optimize
│   │                       #   Toggle: toolbar "💬 Chat" btn or Ctrl+Shift+I
│   │
│   ├── core/               # Shared utilities
│   │   ├── languages.py    # Language → file extension mapping
│   │   ├── platform.py     # OS detection helpers
│   │   └── project.py      # Project-level helpers
│   │
│   ├── dsa/                # ★ DSA Practice module
│   │   ├── bank.py         # Question dataclass + get_all_questions()
│   │   │                   #   SQLite DB: app/dsa/questions.db (gitignored)
│   │   │                   #   Re-seed: seed(force=True)
│   │   ├── seed_questions.py  # 187 questions across 21 topics
│   │   │                      # Sources: Striver SDE Sheet + NeetCode 150
│   │   ├── panel.py        # DSAPanel(QWidget) — left sidebar
│   │   │                   #   Sheet filter, topic tree, progress bars
│   │   │                   #   Emits question_selected signal
│   │   ├── starters.py     # Generates starter code for 11 languages
│   │   │                   #   make_full_editor_content(question, language)
│   │   │                   #   Includes comment block header + skeleton
│   │   ├── checker.py      # Groq AI solution checker
│   │   │                   #   check_solution_async() → CheckResult
│   │   │                   #   Returns: verdict, issues, edge_cases,
│   │   │                   #            complexity_ok, hint
│   │   └── storage.py      # SQLite solutions DB
│   │                       #   ~/.local/share/nitin-editor/solutions.db
│   │                       #   save_solution(), get_solution()
│   │                       #   get_sheet_progress(), get_topic_progress()
│   │
│   ├── sql/
│   │   ├── executor.py     # SQLExecutor — runs SQLite queries, returns SQLResult
│   │   └── formatter.py    # Format SQL result as HTML table for output panel
│   │
│   ├── terminal/
│   │   ├── console.py      # TerminalConsole(QWidget) — integrated terminal UI
│   │   ├── command_runner.py  # CommandRunner — subprocess shell execution
│   │   ├── command_reference.py  # Built-in command help / cross-platform equivalents
│   │   ├── history.py      # Terminal command history (persist to disk)
│   │   └── safety.py       # Dangerous command detection (rm -rf etc.)
│   │
│   ├── platform/
│   │   └── terminal_backend.py  # OS-specific terminal backend detection
│   │
│   └── ui/
│       └── settings_dialog.py   # Settings/Preferences dialog (QDialog)
│
├── tests/                  # pytest test suite — 74 tests, all passing
│   ├── conftest.py         # Shared fixtures (headless Qt app)
│   ├── test_dsa_bank.py    # DSA question bank validation
│   ├── test_dsa_checker.py # CheckResult / hint field tests
│   ├── test_dsa_starters.py# Starter code generation (11 langs × topics)
│   ├── test_dsa_storage.py # Sheet/topic progress queries
│   ├── test_compiler.py    # Language detection, HTML runner
│   ├── test_ai_transpiler.py  # Transpiler prompt building
│   ├── test_runner_thread.py  # RunnerThread signal tests
│   ├── test_sql.py         # SQL executor + formatter
│   ├── test_terminal.py    # Terminal safety + history
│   ├── test_gui_headless.py   # Full app window smoke test
│   ├── test_ide_ux.py      # UX: tab open, close, language switch
│   ├── test_interactive.py # stdin/interactive run mode
│   └── test_languages.sh   # Shell: compile+run test for each language
│
└── scripts/
    └── generate_and_install_icons.py  # Icon generation helper
```

---

## UI Layout (visual map)

```
┌─────────────────────────────── NitinEditor (QMainWindow) ────────────────────────────────┐
│  Menubar: File  Edit  View  Run  Terminal  Tabs  Settings  🧩DSA  💬Chat  Help            │
├─────────────────────────────────────────────────────────────────────────────────────────── │
│  Toolbar: [New][Open][Save] | Language▼ | [▶RUN][■STOP][🌐Preview][🌍Browser]             │
│           | [🎯Check Solution (DSA only)] | [💬Chat] | [⚙]                                │
├──────────────┬──────────────────────────────────────────────┬───────────────────────────── │
│              │                                              │                             │
│  DSAPanel    │         QTabWidget (editor tabs)             │   ChatbotPanel              │
│  (left)      │                                              │   (right)                   │
│  hidden by   │   ┌─ Tab1 ──┬─ Tab2 ──┬─ Tab3 ──┐           │   hidden by default         │
│  default     │   │ editor  │ editor  │ editor  │           │   toggle: Ctrl+Shift+I      │
│              │   │ (Code-  │         │         │           │                             │
│  Ctrl+Shift+D│   │  Editor)│         │         │           │   [🤖 AI Chatbot] [🗑Clear] │
│              │   └─────────┴─────────┴─────────┘           │   [📄 context label]        │
│  Shows:      │                                              │   ┌─────────────────────┐  │
│  - Sheets    │   ── QSplitter (vertical) ──                 │   │ chat bubbles        │  │
│  - Topics    │                                              │   │ user: right purple  │  │
│  - Progress  │   ┌──────────────────────────────────────┐   │   │ AI:   left green    │  │
│  - Questions │   │  Bottom QTabWidget                   │   │   └─────────────────────┘  │
│              │   │  PROBLEMS | OUTPUT | TERMINAL |       │   │   [💡Explain][🐛Debug]    │
│              │   │  🎯 DSA FEEDBACK                      │   │   [⚡Optimize]             │
│              │   └──────────────────────────────────────┘   │   [input_________] [Send]  │
└──────────────┴──────────────────────────────────────────────┴───────────────────────────── │
│  Status bar: Ready | Language | Ln,Col | Spaces:4 | UTF-8                                  │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Running Code

```
User presses Ctrl+Enter
    │
    ▼
NitinEditor._run_code()
    │ reads editor text, current language
    ▼
compiler.compile_code(language, code)
    │ returns: command[], temp_file_path, env
    ▼
RunnerThread(QThread)
    │ subprocess.Popen(command)
    │ streams stdout/stderr via signals
    ▼
NitinEditor._on_output() → Output panel
```

## Data Flow: DSA Check

```
User presses Ctrl+Shift+G
    │
    ▼
NitinEditor._dsa_check_solution()
    │ reads editor code, active question
    ▼
dsa/checker.check_solution_async()
    │ background thread
    │ POST → https://api.groq.com/openai/v1/chat/completions
    │ model: qwen/qwen3.8-27b
    ▼
CheckResult { verdict, issues, complexity_ok, hint }
    │
    ▼
DSA FEEDBACK panel (bottom tabs)
```

## Data Flow: Chatbot

```
User types message → Send
    │
    ▼
ChatbotPanel._send_message(user_text)
    │ context = current tab code (≤200 lines) + filename + language
    │ history = last 20 messages
    ▼
_GroqWorker(QThread)
    │ POST → https://api.groq.com/openai/v1/chat/completions
    │ model: qwen/qwen3.8-27b
    ▼
Reply → right side panel as green AI bubble
```

---

## Key Constants & Config

| What | Value | File |
|---|---|---|
| Groq API URL | `https://api.groq.com/openai/v1/chat/completions` | `chatbot.py`, `checker.py`, `ai_transpiler.py` |
| Groq model | `qwen/qwen3.8-27b` | same files |
| Settings file | `~/.config/nitin-editor/settings.json` | `settings.py` |
| Solutions DB | `~/.local/share/nitin-editor/solutions.db` | `dsa/storage.py` |
| Questions DB | `app/dsa/questions.db` *(gitignored, auto-created)* | `dsa/bank.py` |
| Total DSA questions | **187** (21 topics, Striver + NeetCode) | `dsa/seed_questions.py` |
| Test suite | **74 tests**, all passing | `tests/` |
| Python dep | `PySide6 >= 6.6.0` only | `requirements.txt` |

---

## Supported Languages (18+)

`Python` · `C++` · `C` · `Java` · `JavaScript` · `TypeScript` · `Go` · `Rust` · `Ruby` · `Kotlin` · `Swift` · `PHP` · `Bash` · `R` · `Lua` · `Perl` · `Scala` · `HTML/CSS` · `SQL`

---

## Git

- **Repo:** `https://github.com/nitinsingh2006/ncode.git`
- **Branch:** `main`
- **Run tests:** `python3 -m pytest tests/ -q`
