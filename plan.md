# ncode — DSA Practice Feature: Execution Plan

## 1. Overview and Goals

Add ~120 more questions to the existing DSA Practice feature so the question bank covers the full **Striver's SDE Sheet** (~180 questions) and **NeetCode 150** (~150 questions, significant overlap). Ensure robust test coverage for all layers (storage, checker parser, question bank validation, comment-block generation). Ensure zero regressions on existing functionality.

**What already exists (do NOT recreate):**
- `app/dsa/` module with bank, checker, panel, starters, storage, seed_questions
- 61 questions already seeded in `app/dsa/questions.db`
- DSA sidebar panel, feedback panel, check solution flow, save dialog, progress tracking
- 52 passing tests (16 DSA-related: 8 checker + 8 storage)
- README already documents DSA usage

**What this plan adds:**
- ~120 new questions (batches of 15-20) to reach ~180 total
- Additional tests: question bank validation, comment-block generation per language
- Update README question count
- Final regression

---

## 2. Codebase Findings

### 2.1 File/Folder Tree

```
ncode/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main window (NitinEditor), entry point, DSA integration
│   ├── editor.py             # CodeEditor widget, syntax highlighters (28 languages)
│   ├── compiler.py           # Language definitions, compilation, execution
│   ├── runner.py             # RunnerThread (QThread for code execution)
│   ├── ai_transpiler.py      # Groq AI code transpilation (urllib, threading)
│   ├── settings.py           # Config: load/save JSON, CONFIG_DIR, API keys
│   ├── diagnostics.py        # Diagnostic parsing
│   ├── preview.py            # HTML preview panel
│   ├── terminal.py           # Terminal widget
│   ├── core/
│   │   ├── __init__.py
│   │   ├── languages.py      # LANGUAGES list (28), LANGUAGE_EXTENSIONS, EXTENSION_MAP
│   │   ├── platform.py
│   │   └── project.py
│   ├── dsa/
│   │   ├── __init__.py       # Module docstring only
│   │   ├── bank.py           # Question dataclass, SQLite-backed question bank
│   │   ├── checker.py        # Groq AI solution checker (CheckResult, _parse_response)
│   │   ├── panel.py          # DSAPanel sidebar widget (PySide6)
│   │   ├── starters.py       # Comment block + starter code generators per language
│   │   ├── storage.py        # Solution persistence (SQLite), progress tracking
│   │   ├── seed_questions.py # 61 hardcoded questions, seed() function
│   │   └── questions.db      # SQLite DB (auto-generated)
│   ├── sql/
│   │   ├── __init__.py
│   │   ├── executor.py       # SQLite query executor
│   │   └── formatter.py      # ASCII table formatter
│   ├── terminal/
│   │   ├── __init__.py
│   │   ├── command_runner.py
│   │   ├── console.py
│   │   ├── history.py
│   │   ├── safety.py
│   │   └── command_reference.py
│   ├── ui/
│   │   ├── __init__.py
│   │   └── settings_dialog.py
│   └── platform/
│       ├── __init__.py
│       └── terminal_backend.py
├── tests/
│   ├── test_ai_transpiler.py (30 lines)
│   ├── test_compiler.py      (172 lines)
│   ├── test_dsa_checker.py   (169 lines, 8 tests)
│   ├── test_dsa_storage.py   (174 lines, 8 tests)
│   ├── test_gui_headless.py  (241 lines)
│   ├── test_ide_ux.py        (354 lines)
│   ├── test_interactive.py   (181 lines)
│   ├── test_runner_thread.py (71 lines)
│   ├── test_sql.py           (154 lines)
│   └── test_terminal.py      (145 lines)
├── assets/
│   ├── icon.png
│   ├── icon.svg
│   └── nitin-editor.svg
├── scripts/
│   └── generate_and_install_icons.py
├── requirements.txt          # PySide6>=6.6.0
├── README.md
├── run.sh
├── setup.sh
└── .venv/                    # Python 3.14 venv
```

### 2.2 Entry Point and Main Window

- **Entry point:** `app/main.py` → `NitinEditor(QMainWindow)` class, launched via `main()` at bottom of file.
- **Run command:** `python -m app.main` or `bash run.sh`
- **Main window structure:** `NitinEditor.__init__()` → `_setup_window()`, `_build_ui()`, `_apply_settings()`, `_new_tab()`
- `_build_ui()` → `_create_actions()`, `_build_menu_bar()`, `_build_toolbar()`, `_build_central()`, `_build_status_bar()`

### 2.3 Central Layout (How Sidebar/Panels Work)

`_build_central()` at line 961:
```
QVBoxLayout (root)
└── QSplitter (self._h_splitter, Horizontal)
    ├── DSAPanel (self._dsa_panel, width=280, hidden by default)
    └── QWidget (editor_area)
        └── QSplitter (self._v_splitter, Vertical)
            ├── QTabWidget (self._tab_widget — editor tabs)
            └── QTabWidget (self._bottom_tabs)
                ├── PROBLEMS panel
                ├── OUTPUT panel
                ├── TERMINAL panel
                └── 🎯 DSA FEEDBACK panel
```

### 2.4 Editor Tabs

- `_new_tab(title, language, file_path, code)` at line 1423 creates tabs
- Each tab: `QWidget` container with `QVBoxLayout` → `CodeEditor` widget
- `TabState` (line 460) tracks per-tab metadata: `tab_id`, `title`, `language`, `file_path`, `is_modified`, `dsa_question`
- `_tab_states: dict[int, TabState]` maps `id(container)` → `TabState`
- `_current_editor()` returns the active `CodeEditor`
- DSA tabs: `_dsa_open_question()` at line 1145 creates tab with `[DSA] {title}` prefix, sets `state.dsa_question = question`

### 2.5 Language System

- **Language list:** `app/core/languages.py` → `LANGUAGES` (28 entries): Python, C, C++, Java, JavaScript, TypeScript, Rust, Go, Kotlin, Swift, PHP, Ruby, C#, Bash, R, Dart, Lua, Perl, Scala, Haskell, Julia, Zig, Elixir, HTML, CSS, SQL, JSON, YAML, Markdown
- **Extensions:** `LANGUAGE_EXTENSIONS` dict, `EXTENSION_MAP` reverse dict
- **Toolbar combo:** `self._lang_combo` populated from `LANGUAGES` in `_build_toolbar()` at line 905
- **Compiler/runner mapping:** `app/compiler.py` — `get_missing_tools(language)`, language-specific compile+run logic
- **DSA supported languages:** `app/dsa/starters.py` → `SUPPORTED_LANGS = {"Python", "C", "C++", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C#", "Kotlin", "Swift"}`

### 2.6 Groq Integration

- **AI Transpiler:** `app/ai_transpiler.py` — `_call_groq_api(api_key, prompt)` using `urllib.request`, `threading.Thread(daemon=True)`, `transpile_async()` callback pattern
- **DSA Checker:** `app/dsa/checker.py` — `_call_groq(api_key, prompt)` (same urllib pattern), `_parse_response(raw)` with JSON extraction + `<think>` tag stripping, `check_solution_async()` with `on_success`/`on_error` callbacks
- **API key:** Read from `self._settings.get("groq_api_key", "")` or `gemini_api_key` fallback, stored in `~/.config/nitin-editor/settings.json`
- **Error handling:** HTTP 401/403 (invalid key), 429 (rate limit), URLError (no internet), TimeoutError (>30s), generic exception catch
- **Threading:** `threading.Thread(daemon=True)` in both ai_transpiler.py and checker.py. Main thread uses `_Bridge(QObject)` with Qt Signals to receive results safely.
- **Model:** Checker uses `llama-3.3-70b-versatile`, transpiler uses `qwen/qwen3.8-27b`

### 2.7 Config/Settings

- `app/settings.py` → `CONFIG_DIR = ~/.config/nitin-editor/`, `CONFIG_FILE = settings.json`
- `DEFAULTS` dict includes `groq_api_key`, `gemini_api_key` (both empty string)
- `load_settings()`, `save_settings()`, JSON format with migration

### 2.8 Existing SQLite Usage

- **SQL executor:** `app/sql/executor.py` — SQLExecutor class for user SQL queries
- **DSA question bank:** `app/dsa/bank.py` → `DB_PATH = Path(__file__).parent / "questions.db"` — read-only question storage
- **DSA solutions:** `app/dsa/storage.py` → `SOLUTIONS_DB = ~/.config/nitin-editor/dsa_solutions.db` — user solutions with solved/unsolved status

### 2.9 Existing Code Style

- **Naming:** snake_case functions/variables, PascalCase classes, UPPER_CASE constants
- **Typing:** `from __future__ import annotations`, type hints on function signatures, `Optional[T]`, `dict[str, Any]`
- **Docstrings:** Triple-quote, usually one-line. Present on public functions.
- **Signals/Slots:** PySide6 `Signal` (imported as `Sig` in main.py), `connect()` pattern
- **Threading:** `threading.Thread(daemon=True)` for API calls, `_Bridge(QObject)` pattern for thread→UI communication
- **Styling:** Inline stylesheet strings, Catppuccin Mocha color palette (`#1e1e2e` bg, `#cdd6f4` fg, `#89b4fa` accent, etc.)
- **Imports:** `from __future__ import annotations` at top of every module

### 2.10 Existing Tests

- **Framework:** pytest (installed to venv)
- **Run command:** `cd /home/nitin/ncode && .venv/bin/python -m pytest tests/ -q --tb=short`
- **Current count:** 52 tests, all passing
- **DSA tests:**
  - `tests/test_dsa_checker.py` (8 tests): `_parse_response()` with correct/incorrect/error/malformed JSON/fenced JSON/missing fields/`<think>` tags/unknown verdict
  - `tests/test_dsa_storage.py` (8 tests): init_solutions_db, save/get solution, get_solved_ids, get_progress, get_topic_progress, get_sheet_progress, overwrite solution, unsolved tracking. Uses temp DB file via module-level patch.

### 2.11 Risks

- **Seed order:** `seed_questions.py` uses `INSERT OR IGNORE` with auto-increment IDs. Adding questions in later batches is safe (new rows get new IDs).
- **questions.db is bundled:** It lives at `app/dsa/questions.db`. Re-seeding (force=True) clears and re-inserts. Normal seed is no-op if count > 0.
- **Existing tests import from app.dsa modules** — any schema change would break them. The `questions` table schema is already final and should not change.
- **No existing tests for starters.py** — we must add comment-block generation tests.
- **No existing question bank validation test** — we must add one.

---

## 3. Architecture and Design Decisions

### 3.1 Data Format: SQLite (already chosen)

The question bank already uses SQLite (`app/dsa/questions.db`). This is the correct choice:
- Single-file, no external dependency, built into Python stdlib
- Fast queries with search/filter support
- Already integrated with `bank.py` and `seed_questions.py`

### 3.2 DB Schema (already exists — DO NOT CHANGE)

**Questions table** (in `app/dsa/bank.py:init_db()`):
```sql
CREATE TABLE IF NOT EXISTS questions (
    id                INTEGER PRIMARY KEY,
    title             TEXT NOT NULL,
    source            TEXT NOT NULL,        -- "Striver" | "NeetCode" | "Both"
    topic             TEXT NOT NULL,        -- "Arrays", "Linked List", etc.
    difficulty        TEXT NOT NULL,        -- "Easy" | "Medium" | "Hard"
    problem_statement TEXT NOT NULL,
    examples          TEXT NOT NULL DEFAULT '',
    constraints       TEXT NOT NULL DEFAULT '',
    time_complexity   TEXT NOT NULL DEFAULT '',
    space_complexity  TEXT NOT NULL DEFAULT '',
    lc_number         INTEGER NOT NULL DEFAULT 0,
    tags              TEXT NOT NULL DEFAULT ''
);
```

**Solutions table** (in `app/dsa/storage.py:init_solutions_db()`):
```sql
CREATE TABLE IF NOT EXISTS solutions (
    question_id  INTEGER PRIMARY KEY,
    language     TEXT    NOT NULL DEFAULT 'Python',
    code         TEXT    NOT NULL DEFAULT '',
    solved       INTEGER NOT NULL DEFAULT 0,
    saved_at     TEXT    NOT NULL DEFAULT ''
);
```

### 3.3 Module Diagram (already built)

```
app/dsa/
├── bank.py           # Question dataclass, DB reads (get_all, search, etc.)
├── checker.py        # Groq AI checker (_build_check_prompt, _parse_response, check_solution_async)
├── panel.py          # DSAPanel sidebar widget (QWidget, signals)
├── starters.py       # Comment block + starter code per language
├── storage.py        # Solution persistence (save/get/progress)
└── seed_questions.py # Question data + seed() function — THIS IS WHERE WE ADD QUESTIONS
```

### 3.4 Data Flow (already implemented)

```
User clicks question in DSAPanel
  → panel.question_selected signal
  → NitinEditor._dsa_open_question(question)
  → get_solution(question.id) → check for saved solution
  → make_full_editor_content(question, lang, saved_code)
  → _new_tab(title, language, code) → opens editor tab

User clicks "Check Solution"
  → NitinEditor._dsa_check_solution()
  → _extract_user_code(full_code, lang)
  → check_solution_async(..., api_key, on_success, on_error)
  → background thread → _call_groq() → _parse_response()
  → _Bridge signal → _dsa_on_check_done(result)
  → If correct → _dsa_offer_save(question) → save_solution()
  → panel.mark_solved(question.id)
```

---

## 4. Final File List

### Files to MODIFY:
| File | Purpose |
|------|---------|
| `app/dsa/seed_questions.py` | Add ~120 new questions in the `QUESTIONS` list |
| `README.md` | Update question count from 61 to ~180 |

### Files to CREATE:
| File | Purpose |
|------|---------|
| `tests/test_dsa_bank.py` | Question bank validation: all fields present, unique IDs, valid enums |
| `tests/test_dsa_starters.py` | Comment-block generation tests for all 11 supported languages |

### Files UNCHANGED (no modification needed):
- `app/dsa/bank.py` — schema and query functions are complete
- `app/dsa/checker.py` — already has full prompt, parser, error handling
- `app/dsa/panel.py` — already has search, filters, progress, green ticks
- `app/dsa/starters.py` — already supports 11 languages
- `app/dsa/storage.py` — already has save/get/progress
- `app/main.py` — already has full DSA integration
- All existing test files — must NOT be modified

---

## 5. Question Bank Data Spec

### 5.1 Question Tuple Format (in `seed_questions.py`)

Each question is a tuple in the `QUESTIONS` list:
```python
(title, source, topic, difficulty, lc_number,
 problem_statement, examples, constraints, time_complexity, space_complexity, tags)
```

- `title`: str — problem name (e.g. "Two Sum")
- `source`: "Striver" | "NeetCode" | "Both"
- `topic`: one of the standard topics (see below)
- `difficulty`: "Easy" | "Medium" | "Hard"
- `lc_number`: int — LeetCode problem number (0 if not a LeetCode problem)
- `problem_statement`: str — problem description in own words
- `examples`: str — input/output examples
- `constraints`: str — input constraints
- `time_complexity`: str — required/expected time complexity (e.g. "O(n)")
- `space_complexity`: str — required/expected space complexity
- `tags`: str — comma-separated tags

### 5.2 Standard Topics

Currently used (15 topics): Arrays, Backtracking, Binary Search, Bit Manipulation, Dynamic Programming, Graphs, Hashing, Heap, Linked List, Math, Sliding Window, Sorting, Stack, Trees, Two Pointers

Additional topics needed for remaining questions: Strings, Greedy, Tries, Intervals, Matrix, Design

### 5.3 Fully Written Example Question

```python
(
    "Valid Anagram", "Both", "Strings", "Easy", 242,
    "Given two strings s and t, return true if t is an anagram of s, and false otherwise.\n"
    "An anagram is a word or phrase formed by rearranging the letters of a different word or phrase, "
    "using all the original letters exactly once.",
    "Input: s = \"anagram\", t = \"nagaram\"\nOutput: true\n\n"
    "Input: s = \"rat\", t = \"car\"\nOutput: false",
    "1 <= s.length, t.length <= 5 * 10^4\ns and t consist of lowercase English letters.",
    "O(n)", "O(1) (26 letters)",
    "sorting,character count,hash map"
),
```

### 5.4 Batch Strategy

Questions are added to the `QUESTIONS` list in `seed_questions.py` in batches of ~15-20. The existing 61 are Batch 0. New batches:

| Batch | Topic(s) | ~Count | Notes |
|-------|----------|--------|-------|
| 1 | Strings + Hashing | 15 | Valid Anagram, Encode/Decode, Longest Palindromic Substring, etc. |
| 2 | Arrays + Two Pointers | 15 | 4Sum, Next Permutation, Set Matrix Zeroes, Spiral Matrix, etc. |
| 3 | Binary Search + Sorting | 15 | Median of Two Sorted Arrays, Search 2D Matrix, Non-overlapping Intervals, etc. |
| 4 | Linked List + Stack | 15 | Reorder List, LRU Cache, Largest Rectangle Histogram, etc. |
| 5 | Trees + Tries | 18 | Construct from Preorder/Inorder, Kth Smallest in BST, Implement Trie, Word Search II, etc. |
| 6 | Graphs | 15 | Word Ladder, Alien Dictionary, Network Delay Time, Min Cost to Connect Points, etc. |
| 7 | Dynamic Programming (Part 1) | 18 | Unique Paths, Decode Ways, Palindromic Substrings, Edit Distance, Partition Equal Subset Sum, etc. |
| 8 | Dynamic Programming (Part 2) + Greedy + Intervals | 15 | Burst Balloons, Target Sum, Jump Game I/II, Meeting Rooms, etc. |
| 9 | Backtracking + Matrix + Design + Bit Manipulation + Math + Heap | 15 | Word Search, Rotate Image, Letter Combinations, Missing Number, Happy Number, Task Scheduler, etc. |

Total new: ~141 questions → grand total ~202 unique questions covering both sheets.

### 5.5 Rules for Writing Questions

1. **Do NOT copy proprietary text verbatim.** Rewrite problem statements in your own words while preserving the mathematical/logical meaning.
2. **Every question MUST have all fields non-empty:** title, source, topic, difficulty, problem_statement, examples, constraints, time_complexity, space_complexity. `lc_number` may be 0, `tags` may be empty but should include at least one tag.
3. **Source values:** Use "Both" when a question appears in both Striver's SDE Sheet and NeetCode 150. Use "Striver" or "NeetCode" for sheet-exclusive questions.
4. **Topic values:** Use existing topic names exactly. If introducing a new topic (Strings, Greedy, Tries, Intervals, Matrix, Design), spell it exactly as listed.
5. **Difficulty values:** Must be exactly one of "Easy", "Medium", "Hard".
6. **Examples:** Include at least 2 examples with Input/Output format.
7. **Constraints:** Include all relevant constraints on input size and values.
8. **Complexity:** State expected optimal complexity.
9. **Avoid duplicates:** Check by title AND lc_number. The 61 existing questions use `INSERT OR IGNORE` on auto-increment primary key, so duplicates are naturally prevented.
10. **Question IDs:** Auto-increment. Do NOT manually assign IDs.

### 5.6 Validation Script

A test (`tests/test_dsa_bank.py`) will validate every question after seeding. See Task 2 for details.

---

## 6. Groq Prompt Design (Already Implemented)

The prompt and parser are already complete in `app/dsa/checker.py`. Documenting here for reference.

### 6.1 System Prompt (line 132-136)
```
You are a strict competitive programming judge.
Respond ONLY with valid JSON as instructed.
Never include markdown code fences around the JSON.
```

### 6.2 User Prompt Template (`_build_check_prompt`, line 33-75)
```
You are an expert competitive programming judge.

PROBLEM: {title}
---
{problem}
---
CONSTRAINTS: {constraints}
REQUIRED TIME COMPLEXITY: {req_time}
REQUIRED SPACE COMPLEXITY: {req_space}

USER'S {LANGUAGE} SOLUTION:
```{language}
{code}
```

Evaluate the solution strictly. Respond with ONLY a valid JSON object:
{
  "verdict": "correct" | "incorrect",
  "message": "...",
  "issues": ["..."],
  "edge_cases": ["..."],
  "complexity_ok": true | false,
  "complexity_note": "...",
  "hint": "..."
}
```

### 6.3 JSON Schema

```json
{
  "verdict": "correct | incorrect",
  "message": "string",
  "issues": ["string"],
  "edge_cases": ["string"],
  "complexity_ok": "boolean",
  "complexity_note": "string",
  "hint": "string"
}
```

### 6.4 Parsing Algorithm (`_parse_response`, line 78-123)

1. Strip `<think>...</think>` tags (Qwen/DeepSeek reasoning models) using regex
2. Search for `{...}` JSON object in response using `re.search(r"\{.*\}", raw, re.DOTALL)`
3. If no match → return `CheckResult(verdict="error", ...)`
4. Parse with `json.loads()`. On `JSONDecodeError` → return error result
5. Validate `verdict` — if not "correct" or "incorrect", default to "incorrect"
6. Extract all fields with `.get()` defaults: empty list for arrays, empty string for strings, False for booleans

**Fallbacks already handled:**
- Fenced JSON (`json ... `): the `re.search(r"\{.*\}", ...)` pattern extracts the JSON object from inside fences
- `<think>` tags: stripped by regex
- Missing fields: `.get()` with defaults
- Non-JSON response: returns error verdict
- Empty code: checked before API call in `check_solution_async()`

---

## 7. UI Spec (Already Implemented)

All UI components are already built and functional. Documenting for reference.

### 7.1 Widget Hierarchy
```
NitinEditor (QMainWindow)
├── QMenuBar
│   └── 🧩 DSA menu (Toggle Sidebar, Check Solution, Refresh)
├── QToolBar
│   └── "🎯 Check Solution" button (self._dsa_submit_btn, visible when DSA tab active)
├── QSplitter (horizontal)
│   ├── DSAPanel (left sidebar, 280px, hidden by default)
│   │   ├── Header (🧩 DSA Practice + refresh button)
│   │   ├── Progress section (solved X/Y, percentage, bar, per-sheet stats)
│   │   ├── Filter section (search box, sheet combo, difficulty combo, status combo, topic combo)
│   │   ├── QListWidget (question list with topic separators, green ticks, difficulty icons)
│   │   └── Footer (X questions shown)
│   └── Editor area (vertical splitter)
│       ├── QTabWidget (editor tabs)
│       └── Bottom tabs
│           └── 🎯 DSA FEEDBACK panel (QPlainTextEdit, read-only)
```

### 7.2 Signals/Slots
- `DSAPanel.question_selected(object)` → `NitinEditor._dsa_open_question(question)`
- `_dsa_submit_btn.clicked` → `NitinEditor._dsa_check_solution()`
- `_Bridge.success(object)` → `_dsa_on_check_done(result)`
- `_Bridge.error(str)` → `_dsa_on_check_error(msg)`
- `_tab_widget.currentChanged` → `_on_tab_changed()` → updates `_active_dsa_question` and submit button visibility

### 7.3 Green Tick Rendering
In `DSAPanel._make_question_item()` (panel.py line 431):
- Solved: `"✅ "` prefix, foreground color set to `_GREEN` (#a6e3a1)
- Unsolved: `"   "` prefix (3 spaces), foreground set to difficulty color

### 7.4 Progress Display
- Overall: `"Solved X / Y"` label + percentage + QProgressBar
- Per-sheet: `"Striver: X/Y  ·  NeetCode: X/Y"` label
- Topic separators in list: `"📂 {topic} ({solved}/{total})"`
- Details dialog: `_show_progress_dialog()` with HTML table of all topics

### 7.5 Save Dialog
`_dsa_offer_save()` (main.py line 1345): QMessageBox with "Save" and "Skip" buttons.

### 7.6 Feedback Panel
Bottom tabs → "🎯 DSA FEEDBACK" tab. Shows:
- Question info on open
- "Checking..." message during API call
- Correct: ✅ banner + complexity note + "Great work!"
- Incorrect: ❌ banner + issues list + edge cases + complexity analysis + hint

---

## 8. Step-by-Step Execution Checklist

### Task 1: Create question bank validation tests
- [x] **Task ID:** T1
- **Title:** Add `tests/test_dsa_bank.py` — Question bank validation
- **Files touched:** CREATE `tests/test_dsa_bank.py`
- **Instructions:**
  Create `tests/test_dsa_bank.py` with the following tests:
  ```python
  """
  ncode — DSA Question Bank Validation Tests
  Ensures all questions have required fields, valid enums, and unique IDs.
  """
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).parent.parent))

  from app.dsa.bank import get_all_questions, Question, init_db
  from app.dsa.seed_questions import seed

  VALID_SOURCES = {"Striver", "NeetCode", "Both"}
  VALID_DIFFICULTIES = {"Easy", "Medium", "Hard"}
  VALID_TOPICS = {
      "Arrays", "Backtracking", "Binary Search", "Bit Manipulation",
      "Dynamic Programming", "Graphs", "Greedy", "Hashing", "Heap",
      "Intervals", "Linked List", "Math", "Matrix", "Sliding Window",
      "Sorting", "Stack", "Strings", "Trees", "Tries", "Two Pointers",
      "Design",
  }

  def setup_module():
      init_db()
      seed()

  def test_questions_exist():
      questions = get_all_questions()
      assert len(questions) >= 61, f"Expected >= 61 questions, got {len(questions)}"

  def test_unique_ids():
      questions = get_all_questions()
      ids = [q.id for q in questions]
      assert len(ids) == len(set(ids)), "Duplicate question IDs found"

  def test_unique_titles():
      questions = get_all_questions()
      titles = [q.title for q in questions]
      assert len(titles) == len(set(titles)), f"Duplicate titles found: {[t for t in titles if titles.count(t) > 1]}"

  def test_all_required_fields_present():
      questions = get_all_questions()
      for q in questions:
          assert q.title.strip(), f"Question {q.id} has empty title"
          assert q.source.strip(), f"Question {q.id} ({q.title}) has empty source"
          assert q.topic.strip(), f"Question {q.id} ({q.title}) has empty topic"
          assert q.difficulty.strip(), f"Question {q.id} ({q.title}) has empty difficulty"
          assert q.problem_statement.strip(), f"Question {q.id} ({q.title}) has empty problem_statement"
          assert q.time_complexity.strip(), f"Question {q.id} ({q.title}) has empty time_complexity"
          assert q.space_complexity.strip(), f"Question {q.id} ({q.title}) has empty space_complexity"

  def test_valid_source_values():
      questions = get_all_questions()
      for q in questions:
          assert q.source in VALID_SOURCES, f"Question {q.id} ({q.title}) has invalid source: {q.source}"

  def test_valid_difficulty_values():
      questions = get_all_questions()
      for q in questions:
          assert q.difficulty in VALID_DIFFICULTIES, f"Question {q.id} ({q.title}) has invalid difficulty: {q.difficulty}"

  def test_valid_topic_values():
      questions = get_all_questions()
      for q in questions:
          assert q.topic in VALID_TOPICS, f"Question {q.id} ({q.title}) has invalid topic: {q.topic}"

  def test_lc_number_is_non_negative():
      questions = get_all_questions()
      for q in questions:
          assert q.lc_number >= 0, f"Question {q.id} ({q.title}) has negative lc_number"
  ```
- **Acceptance criteria:** All 8 tests pass. The existing 52 tests still pass.
- **Test command:** `.venv/bin/python -m pytest tests/test_dsa_bank.py tests/ -q --tb=short`
- **Note:** The `VALID_TOPICS` set includes topics that will be introduced in later batches. Tests that validate topic values will initially only check against existing topics, but the set is forward-compatible.

### Task 2: Create comment-block and starter code generation tests
- [x] **Task ID:** T2
- **Title:** Add `tests/test_dsa_starters.py` — Comment block + starter code tests
- **Files touched:** CREATE `tests/test_dsa_starters.py`
- **Instructions:**
  Create `tests/test_dsa_starters.py` testing `make_comment_block()`, `make_starter_code()`, and `make_full_editor_content()` from `app/dsa/starters`:
  ```python
  """
  ncode — DSA Starter Code and Comment Block Tests
  Tests comment-block generation for all supported languages and starter code templates.
  """
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).parent.parent))

  from app.dsa.bank import Question
  from app.dsa.starters import (
      make_comment_block, make_starter_code, make_full_editor_content,
      SUPPORTED_LANGS,
  )

  # Create a sample question for all tests
  SAMPLE_Q = Question(
      id=999, title="Test Problem", source="Both", topic="Arrays",
      difficulty="Medium", problem_statement="Given an array, do something.",
      examples="Input: [1,2,3]\nOutput: 6",
      constraints="1 <= n <= 10^5",
      time_complexity="O(n)", space_complexity="O(1)",
      lc_number=1, tags="test",
  )

  def test_supported_langs_set():
      assert "Python" in SUPPORTED_LANGS
      assert "C++" in SUPPORTED_LANGS
      assert "Java" in SUPPORTED_LANGS
      assert "JavaScript" in SUPPORTED_LANGS
      assert len(SUPPORTED_LANGS) >= 11

  def test_comment_block_python():
      block = make_comment_block(SAMPLE_Q, "Python")
      assert block.startswith("# ")
      assert "Test Problem" in block
      assert "O(n)" in block
      assert "O(1)" in block
      assert "CONSTRAINTS:" in block

  def test_comment_block_cpp():
      block = make_comment_block(SAMPLE_Q, "C++")
      assert block.startswith("// ")
      assert "Test Problem" in block

  def test_comment_block_java():
      block = make_comment_block(SAMPLE_Q, "Java")
      assert block.startswith("// ")
      assert "Test Problem" in block

  def test_comment_block_javascript():
      block = make_comment_block(SAMPLE_Q, "JavaScript")
      assert block.startswith("// ")
      assert "Test Problem" in block

  def test_comment_block_c():
      block = make_comment_block(SAMPLE_Q, "C")
      assert block.startswith("// ")

  def test_comment_block_go():
      block = make_comment_block(SAMPLE_Q, "Go")
      assert block.startswith("// ")

  def test_comment_block_rust():
      block = make_comment_block(SAMPLE_Q, "Rust")
      assert block.startswith("// ")

  def test_comment_block_csharp():
      block = make_comment_block(SAMPLE_Q, "C#")
      assert block.startswith("// ")

  def test_comment_block_kotlin():
      block = make_comment_block(SAMPLE_Q, "Kotlin")
      assert block.startswith("// ")

  def test_comment_block_swift():
      block = make_comment_block(SAMPLE_Q, "Swift")
      assert block.startswith("// ")

  def test_comment_block_typescript():
      block = make_comment_block(SAMPLE_Q, "TypeScript")
      assert block.startswith("// ")

  def test_comment_block_contains_all_sections():
      block = make_comment_block(SAMPLE_Q, "Python")
      assert "PROBLEM:" in block
      assert "EXAMPLES:" in block
      assert "CONSTRAINTS:" in block
      assert "REQUIRED COMPLEXITY:" in block
      assert "Source" in block
      assert "Difficulty" in block

  def test_starter_code_python():
      code = make_starter_code(SAMPLE_Q, "Python")
      assert "class Solution" in code
      assert "def test_problem" in code
      assert "pass" in code

  def test_starter_code_cpp():
      code = make_starter_code(SAMPLE_Q, "C++")
      assert "class Solution" in code
      assert "int main()" in code

  def test_starter_code_java():
      code = make_starter_code(SAMPLE_Q, "Java")
      assert "class Solution" in code
      assert "public static void main" in code

  def test_starter_code_javascript():
      code = make_starter_code(SAMPLE_Q, "JavaScript")
      assert "function" in code or "var" in code

  def test_starter_code_all_supported_langs():
      for lang in SUPPORTED_LANGS:
          code = make_starter_code(SAMPLE_Q, lang)
          assert len(code) > 10, f"Starter code for {lang} is too short"

  def test_full_editor_content_without_saved():
      content = make_full_editor_content(SAMPLE_Q, "Python")
      assert "Test Problem" in content  # comment block present
      assert "class Solution" in content  # starter code present

  def test_full_editor_content_with_saved():
      saved = "def my_solution(): return 42"
      content = make_full_editor_content(SAMPLE_Q, "Python", saved_code=saved)
      assert "Test Problem" in content  # comment block present
      assert "def my_solution(): return 42" in content  # saved code present
      assert "class Solution" not in content  # starter code NOT present

  def test_unsupported_lang_fallback():
      code = make_starter_code(SAMPLE_Q, "Lua")
      assert len(code) > 5  # generic fallback should produce something
  ```
- **Acceptance criteria:** All tests pass. Existing 52 tests still pass.
- **Test command:** `.venv/bin/python -m pytest tests/test_dsa_starters.py tests/ -q --tb=short`

### Task 3: Add question batch 1 — Strings + Hashing
- [x] **Task ID:** T3
- **Title:** Add ~15 questions: Strings + Hashing topics
- **Files touched:** MODIFY `app/dsa/seed_questions.py`
- **Instructions:**
  Append ~15 new question tuples to the `QUESTIONS` list in `seed_questions.py`. These should cover:
  - **Strings:** Valid Anagram (LC 242), Longest Palindromic Substring (LC 5), Palindromic Substrings (LC 647), Encode and Decode Strings (LC 271), Group Anagrams duplicate check (already exists — skip), Longest Common Prefix (LC 14), String to Integer (atoi) (LC 8)
  - **Hashing (additional):** Valid Sudoku (LC 36), Longest Consecutive Sequence (LC 128), Encode and Decode TinyURL (LC 535), Subarray Sum Equals K (LC 560)
  - Plus 4-5 more from either sheet to reach ~15 new questions
  
  After adding, delete `app/dsa/questions.db` and run: `.venv/bin/python -c "from app.dsa.seed_questions import seed; seed(force=True)"`
  
  Then verify: `.venv/bin/python -c "from app.dsa.bank import get_all_questions; print(len(get_all_questions()))"`
- **Acceptance criteria:** Total question count ≥ 76. All tests pass including bank validation.
- **Test command:** `.venv/bin/python -m pytest tests/ -q --tb=short`

### Task 4: Add question batch 2 — Arrays + Two Pointers
- [x] **Task ID:** T4
- **Title:** Add ~15 questions: Arrays + Two Pointers topics
- **Files touched:** MODIFY `app/dsa/seed_questions.py`
- **Instructions:**
  Append ~15 new questions. Suggested:
  - **Arrays:** Set Matrix Zeroes (LC 73), Spiral Matrix (LC 54), Rotate Image (LC 48), Next Permutation (LC 31), Pascal's Triangle (LC 118), Majority Element (LC 169), Sort Colors already exists—skip, 4Sum (LC 18), Longest Subarray with Sum K
  - **Two Pointers:** Two Sum II (LC 167), 3Sum Closest (LC 16), Remove Duplicates from Sorted Array (LC 26), Move Zeroes (LC 283)
  
  After adding, delete `app/dsa/questions.db` and re-seed with `force=True`.
- **Acceptance criteria:** Total ≥ 91. All tests pass.
- **Test command:** `.venv/bin/python -m pytest tests/ -q --tb=short`

### Task 5: Add question batch 3 — Binary Search + Sorting
- [x] **Task ID:** T5
- **Title:** Add ~15 questions: Binary Search + Sorting + Intervals topics
- **Files touched:** MODIFY `app/dsa/seed_questions.py`
- **Instructions:**
  Append ~15 new questions:
  - **Binary Search:** Median of Two Sorted Arrays (LC 4), Search a 2D Matrix (LC 74), Find Peak Element (LC 162), Time Based Key-Value Store (LC 981), Search in Rotated Sorted Array II (LC 81)
  - **Sorting:** Insert Interval (LC 57), Non-Overlapping Intervals (LC 435)
  - **Intervals (new topic):** Meeting Rooms (LC 252), Meeting Rooms II (LC 253), Minimum Number of Arrows to Burst Balloons (LC 452)
  - Plus 5 more to reach ~15
  
  Delete `app/dsa/questions.db` and re-seed.
- **Acceptance criteria:** Total ≥ 106. All tests pass.
- **Test command:** `.venv/bin/python -m pytest tests/ -q --tb=short`

### Task 6: Add question batch 4 — Linked List + Stack
- [x] **Task ID:** T6
- **Title:** Add ~15 questions: Linked List + Stack topics
- **Files touched:** MODIFY `app/dsa/seed_questions.py`
- **Instructions:**
  Append ~15 questions:
  - **Linked List:** Reorder List (LC 143), Copy List with Random Pointer (LC 138), Add Two Numbers (LC 2), Find the Duplicate Number (LC 287), LRU Cache (LC 146), Rotate List (LC 61), Flatten a Multilevel Linked List (LC 430/or similar)
  - **Stack:** Evaluate Reverse Polish Notation (LC 150), Largest Rectangle in Histogram (LC 84), Generate Parentheses (LC 22), Car Fleet (LC 853), Trapping Rain Water already exists as Two Pointers—skip
  
  Delete `app/dsa/questions.db` and re-seed.
- **Acceptance criteria:** Total ≥ 121. All tests pass.
- **Test command:** `.venv/bin/python -m pytest tests/ -q --tb=short`

### Task 7: Add question batch 5 — Trees + Tries
- [x] **Task ID:** T7
- **Title:** Add ~18 questions: Trees + Tries topics
- **Files touched:** MODIFY `app/dsa/seed_questions.py`
- **Instructions:**
  Append ~18 questions:
  - **Trees:** Same Tree (LC 100), Subtree of Another Tree (LC 572), Construct Binary Tree from Preorder and Inorder (LC 105), Kth Smallest Element in BST (LC 230), Binary Tree Maximum Path Sum (LC 124), Count Good Nodes in Binary Tree (LC 1448), Symmetric Tree (LC 101)
  - **Tries (new topic):** Implement Trie (LC 208), Design Add and Search Words (LC 211), Word Search II (LC 212)
  - Plus 5-8 more tree or trie questions
  
  Delete `app/dsa/questions.db` and re-seed.
- **Acceptance criteria:** Total ≥ 139. All tests pass.
- **Test command:** `.venv/bin/python -m pytest tests/ -q --tb=short`

### Task 8: Add question batch 6 — Graphs
- [x] **Task ID:** T8
- **Title:** Add ~15 questions: Graphs topics
- **Files touched:** MODIFY `app/dsa/seed_questions.py`
- **Instructions:**
  Append ~15 questions:
  - **Graphs:** Word Ladder (LC 127), Surrounded Regions (LC 130), Graph Valid Tree (LC 261), Number of Connected Components (LC 323), Redundant Connection (LC 684), Network Delay Time (LC 743), Swim in Rising Water (LC 778), Alien Dictionary (LC 269), Min Cost to Connect All Points (LC 1584), Cheapest Flights Within K Stops (LC 787), Reconstruct Itinerary (LC 332), Walls and Gates (LC 286)
  
  Delete `app/dsa/questions.db` and re-seed.
- **Acceptance criteria:** Total ≥ 154. All tests pass.
- **Test command:** `.venv/bin/python -m pytest tests/ -q --tb=short`

### Task 9: Add question batch 7 — Dynamic Programming (Part 1)
- [x] **Task ID:** T9
- **Title:** Add ~18 questions: Dynamic Programming topics
- **Files touched:** MODIFY `app/dsa/seed_questions.py`
- **Instructions:**
  Append ~18 questions:
  - **DP:** Unique Paths (LC 62), Decode Ways (LC 91), House Robber II (LC 213), Palindromic Substrings (LC 647—may overlap with Strings, use DP topic or skip if added), Edit Distance (LC 72), Partition Equal Subset Sum (LC 416), Minimum Path Sum (LC 64), Triangle (LC 120), Best Time to Buy and Sell Stock with Cooldown (LC 309), Distinct Subsequences (LC 115), Interleaving String (LC 97), Maximum Length of Repeated Subarray (LC 718), Matrix Chain Multiplication (classic), Egg Drop Problem (classic)
  
  Delete `app/dsa/questions.db` and re-seed.
- **Acceptance criteria:** Total ≥ 172. All tests pass.
- **Test command:** `.venv/bin/python -m pytest tests/ -q --tb=short`

### Task 10: Add question batch 8 — DP Part 2 + Greedy + Remaining
- [ ] **Task ID:** T10
- **Title:** Add ~15 questions: Remaining DP + Greedy + Design + Matrix + Math + Bit + Heap
- **Files touched:** MODIFY `app/dsa/seed_questions.py`
- **Instructions:**
  Append ~15 questions to fill remaining gaps:
  - **DP:** Burst Balloons (LC 312), Target Sum (LC 494), Regular Expression Matching (LC 10)
  - **Greedy (new topic):** Jump Game (LC 55), Jump Game II (LC 45), Gas Station (LC 134), Hand of Straights (LC 846)
  - **Design (new topic):** Min Stack (already exists — skip), Design Twitter (LC 355), Implement Queue using Stacks (LC 232)
  - **Matrix (new topic):** Rotate Image (may already be in batch 4 under Arrays), Set Matrix Zeroes (may already be in batch 4), Word Search (LC 79)
  - **Math/Bit/Heap extras:** Pow(x,n) already exists — skip, Multiply Strings (LC 43), Task Scheduler (LC 621), Find K Pairs with Smallest Sums (LC 373)
  
  Be careful to skip any questions already added in previous batches (check titles against what's already in `QUESTIONS` list).
  
  Delete `app/dsa/questions.db` and re-seed.
- **Acceptance criteria:** Total ≥ 180. All tests pass. Bank validation test confirms all questions have valid fields.
- **Test command:** `.venv/bin/python -m pytest tests/ -q --tb=short`

### Task 11: Update README
- [ ] **Task ID:** T11
- **Title:** Update README with final question count
- **Files touched:** MODIFY `README.md`
- **Instructions:**
  Find the line in README.md that says "**61+ questions**" and update it to the actual final count (e.g. "**180+ questions**"). Update any other references to question counts.
  
  Find the "Topics:" line and add any new topics introduced (Strings, Greedy, Tries, Intervals, Matrix, Design if they were used).
  
  Keep all other README content unchanged.
- **Acceptance criteria:** README accurately reflects the final question count and topic list.
- **Test command:** `.venv/bin/python -m pytest tests/ -q --tb=short`

### Task 12: Final full regression
- [ ] **Task ID:** T12
- **Title:** Final regression — all tests must pass
- **Files touched:** None (read-only verification)
- **Instructions:**
  1. Run: `.venv/bin/python -m pytest tests/ -q --tb=short`
  2. Verify ALL tests pass (should be 52 original + 8 bank validation + ~22 starters = ~82 total)
  3. Verify question count: `.venv/bin/python -c "from app.dsa.bank import get_all_questions; qs=get_all_questions(); print(f'Total: {len(qs)} questions'); topics={q.topic for q in qs}; print(f'Topics: {sorted(topics)}')"`
  4. Verify the app launches without crash: `.venv/bin/python -c "import sys; sys.path.insert(0,'.'); from app.dsa.bank import get_all_questions; from app.dsa.seed_questions import seed; seed(); qs=get_all_questions(); print(f'OK: {len(qs)} questions, all imports work')"`
- **Acceptance criteria:** All tests pass. Question count ≥ 180. No import errors.
- **Test command:** `.venv/bin/python -m pytest tests/ -v --tb=short 2>&1 | tail -30`

---

## 9. Manual QA Checklist

After all tasks are complete, manually verify (if a GUI environment is available):

1. **Launch app:** `cd /home/nitin/ncode && .venv/bin/python -m app.main`
2. **Toggle DSA sidebar:** `Ctrl+Shift+D` → sidebar appears with question list
3. **Search:** Type "two sum" in search box → filters correctly
4. **Filter by sheet:** Select "Striver" → only Striver/Both questions shown
5. **Filter by difficulty:** Select "Hard" → only Hard questions shown
6. **Filter by status:** Select "Unsolved" → only unsolved shown (all, initially)
7. **Filter by topic:** Select a topic → only that topic's questions shown
8. **Click a question:** Opens in new tab with comment block + starter code
9. **Check language combo:** Should show the correct language for the DSA tab
10. **Switch tabs:** DSA submit button visibility toggles correctly
11. **Progress display:** Shows "Solved 0 / N" with correct N
12. **📊 button:** Shows progress dialog with all topics listed
13. **Check Solution (without API key):** Shows API key warning dialog
14. **Close and reopen app:** Questions persist (SQLite)

---

## 10. Risks, Edge Cases, and Rollback Notes

### Risks
1. **Re-seeding wipes IDs:** `seed(force=True)` deletes all rows and re-inserts. Auto-increment IDs will change. This only affects `questions.db`, NOT `dsa_solutions.db`. However, saved solutions reference `question_id` which may no longer match after re-seed. **Mitigation:** Since the solutions DB is in user's config dir and the questions DB is bundled, this is expected during development. In production, `seed()` (without force) is a no-op if data exists.
2. **Large `QUESTIONS` list:** Adding 120+ tuples makes `seed_questions.py` very long (~1500+ lines). This is acceptable — it's a data file, not logic.
3. **Duplicate titles:** `INSERT OR IGNORE` on auto-increment ID won't prevent duplicates by title. The bank validation test (`test_unique_titles`) will catch this.

### Edge Cases
- Questions with special characters in title/statement (quotes, backslashes) — use raw strings or escape properly
- Empty examples or constraints — avoid but handle gracefully (fields default to '')
- Very long problem statements — keep concise (rewrite in own words)

### Rollback
- To undo: `git revert` the commits or `git checkout` the original `seed_questions.py`
- Questions DB can be regenerated: delete `app/dsa/questions.db` and run `seed(force=True)`
- New test files can be simply deleted with no impact on existing tests

---

## 11. Executor Rules

EXECUTOR RULES:
- Read plan.md fully before starting. Work task by task in order.
- After EACH task: run the existing + new tests; all must pass before
  moving on. If something fails, fix it before continuing.
- Tick the task checkbox in plan.md after finishing it, and add a short
  "Progress log" line at the bottom with the date and what was done, so work
  can resume if the session stops.
- Never skip a task, never change the architecture without a written
  reason in the log, never delete or weaken existing tests.
- Make a git commit after each completed task with a clear message.
- If a name/path in plan.md does not match reality, inspect the code and
  adapt, then note the deviation in the Progress log.
- Be token-efficient: do not re-read files already read, use grep to locate
  code, print only key test results (pass/fail counts and error lines),
  write each file once and use small targeted edits, keep replies to 2-3
  lines per task, and save progress after every task so a quota cutoff never
  loses work.
- Do not do unrelated refactors or extra work outside plan.md.
- Do not stop until every checkbox is ticked and the final regression
  passes. At the end, print a summary of all files created/modified.

---

## Progress Log

_(Executor: add dated entries here as tasks are completed)_

2026-10-27 — T1: added DSA question-bank validation tests.
2026-10-27 — T2: added DSA starter and comment-block tests.
2026-10-27 — T3: added and validated 15 Strings and Hashing questions (76 total).
2026-10-27 — T4: added and validated 15 Arrays and Two Pointers questions (91 total).
2026-10-27 — T5: added and validated 15 Binary Search, Sorting, and Intervals questions (106 total).
2026-10-27 — T6: added and validated 15 Linked List and Stack questions (121 total).
2026-10-27 — T7: added and validated 18 Trees and Tries questions (139 total).
2026-10-27 — T8: added and validated 15 Graphs questions (154 total).
2026-10-27 — T9: added and validated 18 Dynamic Programming questions (172 total).
