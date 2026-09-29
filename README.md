# Nitin Editor

A private, fully local desktop code editor for Ubuntu Linux.

## Features

- **Dark-themed** professional code editor with syntax highlighting
- **Multi-tab** support with close/reopen tabs
- **Runs code** for: Python, C, C++, Java, JavaScript, HTML, CSS
- **Stdin input panel** for interactive programs
- **Output panel** with stdout, stderr, exit code, execution time
- **Stop button** to terminate hanging programs
- **Execution timeout** (configurable, default 10s)
- **Find & Replace** dialog
- **Settings** dialog (theme, font, tab size, timeout)
- **Recent files** list
- **HTML/CSS preview** panel
- **No cloud, no account, no telemetry**

## Launch

```bash
ncode              # Open editor
ncode file.cpp     # Open a specific file
ncode file.py      # Open Python file (auto-detects language)
```

## Supported Languages

| Language   | Extension | Runtime/Compiler |
|------------|-----------|-----------------|
| Python     | .py       | python3         |
| C          | .c        | gcc             |
| C++        | .cpp .cc  | g++             |
| Java       | .java     | javac + java    |
| JavaScript | .js       | node            |
| HTML       | .html     | built-in preview |
| CSS        | .css      | built-in preview |

## Keyboard Shortcuts

| Shortcut      | Action          |
|---------------|-----------------|
| Ctrl+Enter    | Run code        |
| Ctrl+N        | New tab         |
| Ctrl+O        | Open file       |
| Ctrl+S        | Save            |
| Ctrl+Shift+S  | Save As         |
| Ctrl+W        | Close tab       |
| Ctrl+Z / Y    | Undo / Redo     |
| Ctrl+F        | Find            |
| Ctrl+H        | Find & Replace  |
| Ctrl+Shift+P  | HTML/CSS Preview|
| Ctrl+Shift+C  | Stop execution  |

## Project Structure

```
ncode/
├── app/
│   ├── main.py         # Main window & entry point
│   ├── editor.py       # Code editor widget
│   ├── compiler.py     # Language execution engine
│   ├── runner.py       # Background execution thread
│   ├── preview.py      # HTML/CSS preview panel
│   ├── settings.py     # Settings management
│   └── ui/
│       └── settings_dialog.py
├── assets/
│   ├── icon.png
│   └── icon.svg
├── requirements.txt
├── run.sh
├── setup.sh
└── README.md
```

## Configuration

Settings are stored in: `~/.config/nitin-editor/settings.json`
Recent files: `~/.config/nitin-editor/recent_files.json`

## License

Private — for personal use only.
