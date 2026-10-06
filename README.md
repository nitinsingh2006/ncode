# Nitin Editor

A private, fully local desktop code editor for Ubuntu Linux.

## Features

- **Dark-themed** professional code editor with syntax highlighting
- **Multi-tab** support with close/reopen tabs
- **Runs code** for: Python, C, C++, Java, JavaScript, HTML, CSS, SQL
- **SQL Language Support**: Execute SQL scripts locally using SQLite (`.sql`, `.db`, `.sqlite`, `.sqlite3`) with formatted ASCII table output
- **Integrated Terminal**: Execute local shell commands directly from the editor
- **Cross-Platform OS Modes**: 
  - **Linux**: Real command execution via controlled local subprocess
  - **Windows & macOS**: Educational preview & compatibility simulation mode (clearly marked when unavailable)
- **Command Reference**: Educational cross-platform command equivalence reference
- **Terminal History**: Persistent local command history (`~/.config/nitin-editor/terminal_history.json`)
- **Safety Checks**: Confirmation dialog for dangerous system commands (`rm -rf /`, `mkfs`, `dd`, `shutdown`, `reboot`, etc.)
- **Environment Info**: System environment inspector (kernel, shell, compilers, SQLite, runtime versions)
- **Stdin input panel** for interactive programs
- **Output panel** with stdout, stderr, exit code, execution time
- **Stop button** to terminate hanging processes
- **Execution timeout** (configurable, default 10s for code, 30s for terminal)
- **Find & Replace** dialog
- **Settings** dialog (theme, font, tab size, timeout, SQL mode, terminal preferences)
- **Recent files** list
- **HTML/CSS preview** panel
- **No cloud, no account, no telemetry, fully local and offline**

> **Note on OS Modes**: Windows and macOS commands are not actually executed on those operating systems when Nitin Editor is running on Ubuntu. Nitin Editor never fabricates command output.

## Launch

```bash
ncode              # Open editor
ncode file.cpp     # Open a specific file
ncode file.sql     # Open SQL file (auto-detects language)
```

## Supported Languages & Tools

| Language / Tool   | Extension | Runtime / Engine |
|-------------------|-----------|------------------|
| Python            | .py       | python3          |
| C                 | .c        | gcc              |
| C++               | .cpp .cc  | g++              |
| Java              | .java     | javac + java     |
| JavaScript        | .js       | node             |
| SQL               | .sql      | Built-in SQLite  |
| HTML              | .html     | Built-in Preview |
| CSS               | .css      | Built-in Preview |
| Linux Terminal    | N/A       | /bin/bash        |
| macOS Terminal    | N/A       | Educational Ref  |
| Windows Terminal  | N/A       | Educational Ref  |

## Shortcuts

| Shortcut       | Action                   |
|----------------|--------------------------|
| Ctrl+Enter / F5| Run code                 |
| Ctrl+N         | New tab                  |
| Ctrl+O         | Open file                |
| Ctrl+S         | Save                     |
| Ctrl+Shift+S   | Save As                  |
| Ctrl+W         | Close tab                |
| Ctrl+Z / Y     | Undo / Redo              |
| Ctrl+F         | Find                     |
| Ctrl+H         | Find & Replace           |
| Ctrl+Shift+T   | Toggle Terminal Panel    |
| Ctrl+Shift+P   | HTML/CSS Preview         |
| Ctrl+Shift+C   | Stop execution           |

## Testing

```bash
# Run unit & integration test suite
./.venv/bin/python3 tests/test_compiler.py
./.venv/bin/python3 tests/test_runner_thread.py
./.venv/bin/python3 tests/test_sql.py
./.venv/bin/python3 tests/test_terminal.py
./.venv/bin/python3 tests/test_gui_headless.py
bash tests/test_languages.sh
```

## Project Structure

```
ncode/
├── app/
│   ├── main.py             # Main window & entry point
│   ├── editor.py           # Code editor widget & SQL syntax highlighter
│   ├── compiler.py         # Language execution engine
│   ├── runner.py           # Background execution thread
│   ├── preview.py          # HTML/CSS preview panel
│   ├── settings.py         # Settings management
│   ├── sql/
│   │   ├── __init__.py
│   │   ├── executor.py     # SQLite execution engine
│   │   └── formatter.py    # ASCII result table formatter
│   ├── terminal/
│   │   ├── __init__.py
│   │   ├── command_runner.py  # Shell subprocess runner
│   │   ├── command_reference.py # Cross-platform command database
│   │   ├── history.py      # Terminal command history manager
│   │   └── safety.py       # Dangerous command detection
│   └── ui/
│       └── settings_dialog.py
├── assets/
│   ├── icon.png
│   └── icon.svg
├── tests/
│   ├── test_compiler.py
│   ├── test_gui_headless.py
│   ├── test_interactive.py
│   ├── test_languages.sh
│   ├── test_runner_thread.py
│   ├── test_sql.py
│   └── test_terminal.py
├── requirements.txt
├── run.sh
├── setup.sh
└── README.md
```

## Configuration

Settings are stored in: `~/.config/nitin-editor/settings.json`
Recent files: `~/.config/nitin-editor/recent_files.json`
Terminal History: `~/.config/nitin-editor/terminal_history.json`

## Next Release

### Added
- SQL language support with SQLite execution and ASCII result table formatting
- Local SQLite database file opening and selection
- Integrated Terminal panel (Ctrl+Shift+T)
- Real Linux command execution via controlled subprocess
- Windows command compatibility simulation mode
- macOS command compatibility simulation mode
- Educational cross-platform command reference table
- Terminal command history with persistence (`~/.config/nitin-editor/terminal_history.json`)
- Safety check confirmation dialog for dangerous commands
- Environment Information inspector panel
- Extended Settings dialog for SQL and Terminal options

## License

Private — for personal use only.
