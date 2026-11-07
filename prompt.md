# ncode — Full Application Story & AI Continuation Prompt

> **⚠️ RULE FOR ALL AI AGENTS:** Before your quota runs out or session ends, **update this file** with any new features, file changes, or progress. This is the single source of truth for resuming work.

---

## 🧭 What is ncode?

**ncode** is a custom Python/PySide6 code editor built by **Nitin Singh** (`nitinsingh2006`). It is a full-featured IDE with:
- Multi-tab code editing
- 28 languages with syntax highlighting
- Code runner (compile + execute in-editor)
- Integrated terminal
- AI chatbot (Groq-powered, Hinglish-aware)
- DSA Practice (187 questions, Striver + NeetCode)
- GitHub auto-push
- Pomodoro timer
- File tree sidebar
- LeetCode sync

**GitHub:** `https://github.com/nitinsingh2006/ncode`  
**Main branch:** `main`  
**Run command:** `cd /home/nitin/ncode && bash run.sh`  
**Tests:** `cd /home/nitin/ncode && python3 -m pytest tests/ -q` → must always pass (currently **74 tests**)

---

## 📁 File Map (every important file)

```
/home/nitin/ncode/
├── app/
│   ├── main.py              ★ CORE — NitinEditor(QMainWindow), ~3400 lines
│   │                           All UI, tabs, menus, toolbar, signals
│   ├── editor.py            — CodeEditor widget, syntax highlighting (28 langs)
│   ├── compiler.py          — LANGUAGES list, compilation commands, detect_language()
│   ├── runner.py            — RunnerThread (QThread) for code execution
│   ├── settings.py          — load_settings() / save_settings() → ~/.config/nitin-editor/settings.json
│   ├── diagnostics.py       — Error/warning parsing from compiler output
│   ├── preview.py           — HTML live preview panel (QWebEngineView)
│   ├── ai_transpiler.py     — Groq AI code transpiler (urllib, threading)
│   ├── github_pusher.py     ★ GitHub REST API push (urllib only, no deps)
│   │                           push_code_file() | push_dsa_solution()
│   ├── pomodoro.py          ★ Pomodoro timer widget (QTimer, 25/5/15 min)
│   ├── file_tree.py         ★ File tree sidebar (QTreeWidget, folder browsing)
│   ├── chatbot.py           ★ Live AI chatbot panel (Groq qwen/qwen3.8-27b)
│   │                           ChatbotPanel, _CodeBlockWidget (Copy/Editor/Run buttons)
│   │                           Admin Mode: Groq edits ncode files with confirmation
│   ├── core/
│   │   ├── languages.py     — LANGUAGES list (28), LANGUAGE_EXTENSIONS, EXTENSION_MAP
│   │   ├── platform.py      — OS detection
│   │   └── project.py       — Project helpers
│   ├── dsa/
│   │   ├── bank.py          — Question dataclass, SQLite question bank, get_all_questions()
│   │   ├── checker.py       — Groq AI solution checker → CheckResult(verdict, message, issues, hint)
│   │   ├── panel.py         ★ DSAPanel sidebar widget — question list, filters, 🔗 LeetCode button
│   │   ├── starters.py      — Starter code + comment block generator per language (11 langs)
│   │   ├── storage.py       — save_solution() / get_solution() → ~/.config/nitin-editor/dsa_solutions.db
│   │   ├── seed_questions.py — 187 hardcoded questions (Striver SDE + NeetCode 150)
│   │   ├── leetcode_sync.py ★ Title → LeetCode slug map, get_leetcode_url(), open_leetcode()
│   │   └── questions.db     — SQLite (auto-generated, gitignored)
│   ├── sql/
│   │   ├── executor.py      — SQLite query executor
│   │   └── formatter.py     — ASCII table formatter for SQL output
│   ├── terminal/
│   │   ├── command_runner.py — CommandRunner, CommandResult
│   │   ├── console.py        — TerminalConsole widget
│   │   ├── history.py        — Command history (load/save)
│   │   ├── safety.py         — Dangerous command detection
│   │   └── command_reference.py — Command help text
│   ├── platform/
│   │   └── terminal_backend.py
│   └── ui/
│       └── settings_dialog.py ★ SettingsDialog — Appearance, Editor, GitHub section
├── tests/
│   ├── test_ai_transpiler.py
│   ├── test_compiler.py
│   ├── test_dsa_checker.py    — 8 DSA checker tests
│   ├── test_dsa_storage.py    — 8 DSA storage tests
│   ├── test_gui_headless.py
│   ├── test_ide_ux.py
│   ├── test_interactive.py
│   ├── test_runner_thread.py
│   ├── test_sql.py
│   └── test_terminal.py
├── assets/
│   ├── icon.png / icon.svg / nitin-editor.svg
├── scripts/
│   └── generate_and_install_icons.py
├── requirements.txt          — PySide6>=6.6.0 only
├── README.md                 — Full feature docs
├── plan.md                   — DSA question bank expansion plan (all tasks complete)
├── prompt.md                 ★ THIS FILE — AI continuation guide
├── run.sh                    — `cd /home/nitin/ncode && .venv/bin/python -m app.main`
├── setup.sh                  — Full setup (venv, deps, compilers, desktop icon)
└── install.sh                — One-liner curl installer
```

---

## ⚙️ Settings File

**Location:** `~/.config/nitin-editor/settings.json`

**All keys:**
```json
{
  "theme": "dark",
  "font_size": 14,
  "tab_size": 4,
  "word_wrap": false,
  "execution_timeout": 10,
  "sql_db_mode": "Memory",
  "sql_auto_cleanup": true,
  "terminal_default_os": "Linux",
  "terminal_timeout": 30,
  "terminal_history_size": 500,
  "terminal_confirm_dangerous": true,
  "groq_api_key": "gsk_...",
  "gemini_api_key": "gsk_...",
  "github_repo": "https://github.com/username/my-code",
  "github_token": "ghp_...",
  "dsa_github_repo": "https://github.com/username/dsa-solutions"
}
```

---

## 🌟 All Features (with how they work)

### 1. Code Editor
- **File:** `app/editor.py` — `CodeEditor(QPlainTextEdit)`
- 28 languages, Pygments-based syntax highlighting
- Line numbers, auto-indent, bracket matching
- Find & Replace (`Ctrl+H`)

### 2. Code Runner
- **File:** `app/runner.py` — `RunnerThread(QThread)`
- Run with `Ctrl+Enter` / `F5`
- Output in bottom "OUTPUT" panel
- Stop with `Ctrl+Shift+C`

### 3. Multi-tab Editor
- **In:** `app/main.py` → `_tab_widget` (QTabWidget)
- Tab state: `TabState` dataclass — `title`, `language`, `is_modified`, `file_path`, `dsa_question`
- Close tab: `_close_tab(index)` — checks unsaved changes, asks GitHub push

### 4. Integrated Terminal
- **File:** `app/terminal/` suite
- Bottom panel "TERMINAL" tab
- Safety checks for dangerous commands
- Command history

### 5. AI Chatbot (Groq)
- **File:** `app/chatbot.py` — `ChatbotPanel(QWidget)`
- Model: `qwen/qwen3.8-27b` (Groq API)
- System prompt: has full ncode knowledge, DSA DB context, Admin Mode
- **Admin Mode:** 🔧 button → Groq can read/edit ncode source files with confirmation dialog
- Code blocks have: `⧉ Copy` | `→ Editor` | `▶ Run Code` | `⚡ Run in Terminal` buttons
- Shortcut: `Ctrl+Shift+I`

### 6. AI Transpiler
- **File:** `app/ai_transpiler.py`
- Converts code between languages via Groq
- Shortcut: `Ctrl+Shift+T`

### 7. DSA Practice
- **Files:** `app/dsa/` — panel, bank, checker, starters, storage, seed_questions, leetcode_sync
- 187 questions (Striver SDE + NeetCode 150), 21 topics
- Opens question in editor with comment block + starter code
- Groq AI checks solution → verdict, issues, complexity, hint
- Tracks progress in SQLite (`dsa_solutions.db`)
- **LeetCode button:** 🔗 opens LeetCode problem in browser
- Shortcut: `Ctrl+Shift+D` (toggle), `Ctrl+Shift+G` (check solution)

### 8. GitHub Integration ★
- **File:** `app/github_pusher.py` (GitHub REST API, urllib only)
- **Settings:** `github_repo`, `dsa_github_repo`, `github_token` (PAT)
- **🐙 Push button** (toolbar, green): one click → smart push
  - DSA question tab → `dsa_github_repo` with `{topic}/{slug}/README.md` + `solution.{ext}`
  - Regular file → `github_repo` under `code/` folder
- **Tab-close prompt:** modified tab closed → asks "Push to GitHub?"
- **DSA save prompt:** correct solution saved → asks "Push DSA to GitHub?"
- **Shortcut:** `Ctrl+Shift+U`
- **Menu:** File → 🐙 Push to GitHub

### 9. Pomodoro Timer ★
- **File:** `app/pomodoro.py` — `PomodoroWidget(QWidget)`
- Bottom panel "🍅 Pomodoro" tab
- 25 min work (red) → 5 min break (green) → 15 min long break every 4
- `QTimer` based (1 second tick), `QApplication.beep()` on session end
- Shortcut: `Ctrl+Shift+O`

### 10. File Tree Sidebar ★
- **File:** `app/file_tree.py` — `FileTreeWidget(QWidget)`
- Left panel "🌳 Files" tab (alongside "🎯 DSA" tab)
- Open folder → recursive tree with emoji icons per file type
- Filter box for live search
- Double-click file → opens in new editor tab
- Skips: `.git`, `__pycache__`, `.venv`, `node_modules`, etc.
- Shortcut / menu: `Ctrl+Shift+F` or toolbar 📁

### 11. SQL Runner
- **File:** `app/sql/executor.py`
- SQLite in-memory or file mode
- Results as ASCII table in OUTPUT panel

### 12. HTML Preview
- **File:** `app/preview.py`
- Live preview in side panel (`Ctrl+Shift+P`)
- Open in browser (`Ctrl+Shift+B`)

---

## 🏗️ Architecture: How main.py is Structured

```
NitinEditor(QMainWindow)
├── __init__()
│   ├── _setup_window()          — window title, size, icon
│   ├── _setup_state()           — _settings, _tab_states, counters
│   ├── _create_actions()        — QAction objects (shortcuts)
│   ├── _build_menu_bar()        — File/Edit/View/Run/DSA/Tools/Help menus
│   ├── _build_toolbar()         — toolbar buttons (New/Open/Save/📁/Run/Stop/DSA/Chat/⚙/🍅/🐙 Push)
│   ├── _build_central()         ★ main layout
│   │   ├── _h_splitter (QSplitter horizontal)
│   │   │   ├── _left_tabs (QTabWidget)  — [🌳 Files | 🎯 DSA]
│   │   │   │   ├── _file_tree (FileTreeWidget)
│   │   │   │   └── _dsa_panel (DSAPanel)
│   │   │   ├── editor_area (QWidget)
│   │   │   │   └── _v_splitter (QSplitter vertical)
│   │   │   │       ├── _tab_widget (QTabWidget) — editor tabs
│   │   │   │       └── _bottom_tabs (QTabWidget)
│   │   │   │           ├── PROBLEMS
│   │   │   │           ├── OUTPUT
│   │   │   │           ├── TERMINAL
│   │   │   │           ├── 🎯 DSA FEEDBACK
│   │   │   │           └── 🍅 Pomodoro
│   │   │   └── _chatbot_panel (ChatbotPanel) — right side, hidden by default
│   └── _build_status_bar()      — language, cursor, spaces, encoding
│
├── Tab management
│   ├── _new_tab(title, language, file_path, code)
│   ├── _close_tab(index)         — save prompt + GitHub push prompt
│   ├── _current_state() → TabState
│   └── _current_editor() → CodeEditor
│
├── File operations
│   ├── _open_file() / _open_file_path(Path)
│   ├── _open_folder() → _file_tree.open_folder()
│   ├── _open_file_from_tree(str) → _open_file_path(Path)
│   ├── _save_file() / _save_file_as()
│   └── _new_tab()
│
├── GitHub operations
│   ├── _github_push_current()    ★ smart push (DSA or regular)
│   ├── _push_tab_to_github_bg()  — background QThread push → code repo
│   ├── _push_dsa_solution_to_github_bg() — background QThread → DSA repo
│   └── _on_github_push_done()    — status bar + error dialog
│
├── DSA operations
│   ├── _dsa_toggle_sidebar()     — toggle _left_tabs DSA tab
│   ├── _dsa_open_question(q)     — open question in new tab with starter code
│   ├── _dsa_check_solution()     — Groq check via _GroqCheckerWorker
│   ├── _dsa_offer_save(q)        — save dialog + GitHub push dialog
│   └── _dsa_feedback_area        — QPlainTextEdit showing verdict
│
├── Chatbot operations
│   ├── _chatbot_toggle()
│   ├── _chatbot_sync_context()   — sends current code to chatbot
│   ├── _chatbot_insert_to_editor()
│   ├── _chatbot_insert_and_run()
│   └── _chatbot_run_terminal_command()
│
└── Settings
    ├── _show_settings() → SettingsDialog
    └── _on_settings_changed() → save_settings()
```

---

## 🔧 How to Edit ncode Code (for AI agents)

### Pattern 1: Add a new feature module
1. Create `app/your_feature.py`
2. Import at top of `app/main.py` (after existing imports)
3. Instantiate in `NitinEditor.__init__()` or `_build_central()`
4. Connect signals to `_your_handler()` methods
5. Add menu action in `_build_menu_bar()` via `_add_menu_action()`
6. Add toolbar button in `_build_toolbar()` as `QPushButton` or `tb_action()`
7. Run `python3 -m pytest tests/ -q` — all 74 must pass
8. `git add -A && git commit -m "feat: ..." && git push`

### Pattern 2: Add a new setting
1. Add field to settings.json (auto-created on first run)
2. Add UI in `app/ui/settings_dialog.py` → `_build_ui()` and `_apply()`
3. Read in main.py via `self._settings.get("key", default)`

### Pattern 3: Add a QThread background worker
```python
class _MyWorker(QThread):
    done = Sig(bool, str)   # Sig = Signal from PySide6.QtCore
    def __init__(self, ...): super().__init__(); ...
    def run(self): ...; self.done.emit(ok, msg)

worker = _MyWorker(...)
worker.done.connect(self._on_my_worker_done)
self._workers = getattr(self, '_workers', [])
self._workers.append(worker)
worker.finished.connect(lambda: self._workers.remove(worker) if worker in self._workers else None)
worker.start()
```

### Pattern 4: Add a bottom panel tab
```python
# In _build_central(), after self._dsa_feedback_panel:
self._my_widget = MyWidget()
self._bottom_tabs.addTab(self._my_widget, "🔥 MyTab")
```

### Pattern 5: Add a left sidebar tab
```python
# In _build_central(), _left_tabs is the QTabWidget:
self._my_sidebar = MySidebarWidget()
self._left_tabs.addTab(self._my_sidebar, "🔖 MySidebar")
```

---

## 📌 Groq AI Details

- **API key location:** `self._settings["groq_api_key"]` (also `gemini_api_key` — same value)
- **Model:** `qwen/qwen3.8-27b` (use this, not llama-3.3-70b — not available on this key)
- **API pattern:** `urllib` only — no `requests`, no `httpx`
- **Endpoint:** `https://api.groq.com/openai/v1/chat/completions`
- **Headers:** `Authorization: Bearer {key}`, `Content-Type: application/json`

---

## 🧪 Test Files Reference

| File | Tests | What it covers |
|------|-------|----------------|
| `test_compiler.py` | ~15 | LANGUAGES list, detect_language, compile commands |
| `test_dsa_checker.py` | 8 | CheckResult parsing, verdict detection |
| `test_dsa_storage.py` | 8 | save_solution, get_solution, progress tracking |
| `test_gui_headless.py` | ~10 | NitinEditor headless instantiation |
| `test_ide_ux.py` | ~20 | Tab ops, file open/save, language switching |
| `test_interactive.py` | ~10 | Code runner, output handling |
| `test_runner_thread.py` | ~5 | RunnerThread signals |
| `test_sql.py` | ~10 | SQLite executor, formatter |
| `test_terminal.py` | ~8 | Safety checks, history, command runner |
| `test_ai_transpiler.py` | ~3 | can_transpile(), mocked Groq |

---

## 🚫 Constraints (NEVER break these)

1. **74 tests must pass** — run after every change
2. **No new pip dependencies** — stdlib + PySide6 only
3. **Groq model:** `qwen/qwen3.8-27b` (not llama-3.3-70b)
4. **GitHub API:** `urllib` only (in `github_pusher.py`)
5. **User language:** Hinglish (mix of Hindi + English) in all user-facing text
6. **Config dir:** `~/.config/nitin-editor/` — never hardcode paths
7. **Commit after each feature** — descriptive message, push to `origin/main`

---

## 📅 Progress Log

| Date | What was done |
|------|---------------|
| 2026-10-27 | DSA question bank: 187 questions (Striver SDE + NeetCode 150), all tests pass |
| 2026-10-27 | Chatbot panel: code blocks with Copy/Editor/Run buttons, Groq system prompt with full ncode knowledge |
| 2026-10-27 | DSA live context in chatbot, Admin Mode (Groq edits ncode files with confirmation) |
| 2026-10-27 | setup.sh, install.sh, README.md, tree.md fully updated |
| 2026-11-07 | GitHub Integration: github_pusher.py, Settings dialog GitHub section, tab-close push prompt, DSA auto-push |
| 2026-11-07 | Pomodoro Timer: app/pomodoro.py, bottom panel tab, Ctrl+Shift+O |
| 2026-11-07 | LeetCode Sync: app/dsa/leetcode_sync.py, 🔗 button in DSA panel, URL in feedback |
| 2026-11-07 | File Tree Sidebar: app/file_tree.py, left QTabWidget (Files + DSA), Ctrl+Shift+F |
| 2026-11-07 | 🐙 Push button in toolbar (green), smart push (DSA→DSA repo, regular→code repo), Ctrl+Shift+U |
| 2026-11-07 | prompt.md created — full AI continuation guide |

---

## 🤖 AI Agent Continuation Instructions

**When picking up this project:**

1. `cd /home/nitin/ncode && git log --oneline -5` — see latest commits
2. `python3 -m pytest tests/ -q` — verify all tests pass
3. Read this `prompt.md` for full context
4. Check `plan.md` for DSA-specific tasks
5. Implement requested feature following patterns above
6. Test after every change, commit after every feature
7. **Before quota runs out:** update the Progress Log table in this file

**User communication style:** Hinglish (Hindi + English mix). Casual, bhai-level.

**Key principle:** Never break existing tests. Never add pip deps. Always commit + push.
