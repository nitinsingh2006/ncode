# Nitin Editor (ncode)

A private, fully local desktop code editor for Ubuntu Linux — with a built-in **DSA Practice** mode, AI code checking, multi-language support, and integrated terminal.

---

## ✨ Features

- **Dark-themed** professional code editor with syntax highlighting for 29 languages
- **Multi-tab** support with close/reopen tabs
- **Runs code** for 25+ languages: Python, C, C++, Java, JavaScript, TypeScript, Go, Rust, and more
- **HTML/CSS/JS Runner & Preview** — 1-click execution in system default browser (Chrome/Firefox) with relative asset path support, plus live in-editor preview window
- **SQL Support**: Execute SQL scripts locally using SQLite with formatted ASCII table output
- **Integrated Terminal**: Execute real shell commands directly from the editor
- **Safety Checks**: Confirmation for dangerous commands (`rm -rf`, `shutdown`, `dd`, etc.)
- **Find & Replace** dialog
- **Settings** (theme, font, tab size, timeout, SQL mode, terminal preferences, API keys)
- **Recent files** list
- **No cloud, no account, no telemetry — fully local and offline** (except Groq API calls)

---

## 🧩 DSA Practice

Practice **Striver's SDE Sheet** and **NeetCode 150** problems directly inside the editor.

### How to use
1. Open the DSA sidebar via **🧩 DSA → Toggle Sidebar** (or `Ctrl+Shift+D`)
2. Browse / search / filter by sheet, topic, difficulty, or solved status
3. Click any question to open it in a new editor tab with:
   - Full problem statement as a formatted comment block
   - Language-specific starter code template
4. Write your solution below the comment
5. Click **🎯 Check Solution** (or `Ctrl+Shift+G`) — Groq AI reviews your code and returns:
   - **Correct / Incorrect** verdict
   - Issues and failing edge cases (if incorrect)
   - Time & space complexity analysis
   - A conceptual hint (not the full answer) if incorrect
6. On a correct verdict, save your solution locally — it reloads next time you open the question

### Question Bank
- **193 questions**, including all **150 NeetCode** sheet questions
- Topics: Arrays, Linked List, Trees, Binary Search, Sliding Window, Stack, Dynamic Programming, Graphs, Two Pointers, Hashing, Heap, Backtracking, Sorting, Math, Bit Manipulation, Strings, Greedy, Tries, Intervals, Matrix, Design
- Each question includes: problem statement, examples, constraints, required time/space complexity

### Progress Tracking
- ✅ Green tick next to solved questions in the list
- Overall progress counter (e.g. `Solved X / Total` and percentage)
- Per-sheet progress indicators (Striver's SDE Sheet & NeetCode 150)
- Per-topic progress counts on topic separators and in the **📊 Details** breakdown dialog
- Filters by sheet, topic, difficulty (Easy/Medium/Hard), and solve status (Solved/Unsolved)

### Saving & Re-editing Solutions
- On receiving a correct verdict from Groq AI, a dialog prompts: *"Your solution is correct! Do you want to save this code with the question?"* with **Save** and **Skip** buttons.
- On **Save**, your solution is persisted in local SQLite storage with language and timestamp.
- Reopening the question loads both the problem statement comment header and your saved solution.
- Solutions can be re-edited, re-checked, and overwritten at any time.

### Storage
Solutions are saved locally at: `~/.config/nitin-editor/dsa_solutions.db`

---

## 🚀 Launch

```bash
./run.sh           # Open editor
./run.sh file.cpp  # Open a specific file
```

---

## 🌐 Supported Languages (29)

| Category | Languages |
|----------|-----------|
| Compiled | C, C++, Java, Rust, Go, Kotlin, Swift, C#, Scala, Dart |
| Scripted | Python, JavaScript, TypeScript, Ruby, Perl, PHP, Bash |
| ML/Data  | R, Julia |
| Systems  | Zig, Elixir, Haskell, Lua |
| Web/Data | HTML, CSS, SQL, JSON, YAML, Markdown |

---

## ⌨️ Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Enter / F5 | Run / Preview code |
| Ctrl+N | New tab |
| Ctrl+O | Open file |
| Ctrl+S | Save |
| Ctrl+Shift+S | Save As |
| Ctrl+W | Close tab |
| Ctrl+Z / Y | Undo / Redo |
| Ctrl+F | Find |
| Ctrl+H | Find & Replace |
| Ctrl+Shift+T | Toggle Terminal Panel |
| Ctrl+Shift+P | HTML/CSS Preview |
| Ctrl+Shift+C | Stop execution |
| **Ctrl+Shift+D** | **Toggle DSA Sidebar** |
| **Ctrl+Shift+G** | **Check DSA Solution** |

---

## 🧪 Testing

```bash
python tests/test_compiler.py        # Compiler & execution engine
python tests/test_dsa_storage.py     # DSA solution storage layer
python tests/test_dsa_checker.py     # DSA AI checker response parser
python tests/test_sql.py             # SQL execution
python tests/test_terminal.py        # Terminal runner
python tests/test_runner_thread.py   # Background runner thread
bash tests/test_languages.sh         # Multi-language shell tests
```

---

## 📁 Project Structure

```
ncode/
├── app/
│   ├── main.py             # Main window & entry point
│   ├── editor.py           # Code editor + 29 syntax highlighters
│   ├── compiler.py         # Language execution engine (25+ languages)
│   ├── runner.py           # Background execution thread
│   ├── ai_transpiler.py    # AI code transpiler (Groq API)
│   ├── preview.py          # HTML/CSS/JS live preview panel
│   ├── settings.py         # Settings management
│   ├── diagnostics.py      # Error diagnostics parser
│   ├── dsa/
│   │   ├── __init__.py
│   │   ├── bank.py         # Question bank (SQLite reader + search)
│   │   ├── storage.py      # Solution persistence & progress tracking
│   │   ├── checker.py      # Groq AI solution checker
│   │   ├── starters.py     # Language-specific starter code templates
│   │   ├── panel.py        # DSA sidebar widget
│   │   ├── seed_questions.py # Question bank seeder (193 questions)
│   │   └── questions.db    # Bundled SQLite question bank
│   ├── sql/
│   │   ├── executor.py     # SQLite execution engine
│   │   └── formatter.py    # ASCII result table formatter
│   ├── terminal/
│   │   ├── command_runner.py
│   │   ├── command_reference.py
│   │   ├── history.py
│   │   └── safety.py
│   └── ui/
│       └── settings_dialog.py
├── tests/
│   ├── test_compiler.py
│   ├── test_dsa_storage.py    # NEW
│   ├── test_dsa_checker.py    # NEW
│   ├── test_sql.py
│   ├── test_terminal.py
│   └── test_runner_thread.py
├── requirements.txt
├── run.sh
├── setup.sh
└── README.md
```

---

## ⚙️ Configuration

| File | Purpose |
|------|---------|
| `~/.config/nitin-editor/settings.json` | App settings |
| `~/.config/nitin-editor/recent_files.json` | Recent files |
| `~/.config/nitin-editor/terminal_history.json` | Terminal history |
| `~/.config/nitin-editor/dsa_solutions.db` | DSA solutions & progress |

> **API Key**: Set your Groq API key in Settings → Preferences. Get a free key at [console.groq.com](https://console.groq.com).

---

## License

MIT — see the LICENSE file.

