# GSD — Nitin Editor

## Status: IN PROGRESS
## Started: 2026-09-30
## Target: Full desktop code editor running on Ubuntu 26.04

---

## Summary

A private local desktop code editor with:
- Python, C, C++, Java, JavaScript, HTML, CSS support
- Dark-themed PySide6 GUI with syntax highlighting
- Multi-tab, stdin/stdout, run/stop, find/replace
- ncode terminal command + .desktop launcher

---

## Milestone 1: Core Application ✅ COMPLETE
**Goal:** Build the full PySide6 application
**Acceptance Criteria:**
- [x] PySide6 editor with custom QSyntaxHighlighter for all 7 languages
- [x] Line numbers, auto-indent, bracket matching, current line highlight
- [x] Multi-tab support with close/reopen
- [x] Input panel (stdin), output panel (stdout/stderr/exit code/time)
- [x] Run button + Ctrl+Enter shortcut
- [x] Stop button with process termination
- [x] Find & Replace dialog
- [x] Settings dialog (theme, font, tab size, timeout)
- [x] Recent files menu
- [x] Full menubar (File/Edit/View/Run/Tabs/Settings/Help)
- [x] Keyboard shortcuts (all required)
- [x] Unsaved changes warning on close

### Slice 1.1: Editor Widget ✅
- [x] Task 1.1.1: Custom CodeEditor with QPlainTextEdit base
- [x] Task 1.1.2: 7 language syntax highlighters (Python, C, C++, Java, JS, HTML, CSS)
- [x] Task 1.1.3: Line number area widget
- [x] Task 1.1.4: Auto-indent with block detection
- [x] Task 1.1.5: Bracket auto-close and skip

### Slice 1.2: Execution Engine ✅
- [x] Task 1.2.1: CodeRunner with subprocess isolation
- [x] Task 1.2.2: Temp directory creation and cleanup
- [x] Task 1.2.3: Timeout handling
- [x] Task 1.2.4: Stdin data pipe
- [x] Task 1.2.5: Compile step for C/C++/Java
- [x] Task 1.2.6: RunnerThread (background QThread)

### Slice 1.3: UI Shell ✅
- [x] Task 1.3.1: Main window layout (editor/input/output splitter)
- [x] Task 1.3.2: Toolbar with language selector
- [x] Task 1.3.3: Status bar (language, cursor, encoding)
- [x] Task 1.3.4: Settings persistence in ~/.config/nitin-editor/

---

## Milestone 2: System Integration ✅ COMPLETE
**Goal:** Install as a proper Ubuntu desktop application

### Slice 2.1: Desktop Launcher ✅
- [x] Task 2.1.1: Application icon (PNG + SVG)
- [x] Task 2.1.2: ~/.local/share/applications/nitin-editor.desktop
- [x] Task 2.1.3: ~/Desktop/Nitin Editor.desktop
- [x] Task 2.1.4: update-desktop-database

### Slice 2.2: Terminal Command ✅
- [x] Task 2.2.1: ~/.local/bin/ncode script
- [x] Task 2.2.2: PATH verification
- [x] Task 2.2.3: ncode [file] argument support

### Slice 2.3: Python Environment ✅
- [x] Task 2.3.1: ~/ncode/.venv creation
- [x] Task 2.3.2: PySide6 6.11.2 installation
- [x] Task 2.3.3: requirements.txt

---

## Milestone 3: Fix Qt Platform Launch 🔄 IN PROGRESS
**Goal:** Get the app to actually launch and display GUI

### Slice 3.1: Qt Platform Plugin Fix
- [ ] Task 3.1.1: Install libxcb-cursor0 (needs sudo)
- [ ] Task 3.1.2: Update ncode to auto-detect Wayland/X11
- [ ] Task 3.1.3: Verify GUI launches
- [ ] Task 3.1.4: Test on Wayland (QT_QPA_PLATFORM=wayland)

### Slice 3.2: Java Support
- [ ] Task 3.2.1: Install openjdk-21-jdk (needs sudo)
- [ ] Task 3.2.2: Verify javac/java in PATH
- [ ] Task 3.2.3: Test Java Hello World in editor

---

## Milestone 4: Full Testing ⏳ PENDING
**Goal:** Verify all features work end-to-end

### Slice 4.1: Language Testing
- [ ] Task 4.1.1: Python Hello World → verify output
- [ ] Task 4.1.2: C Hello World → verify output
- [ ] Task 4.1.3: C++ Hello World → verify output
- [ ] Task 4.1.4: Java Hello World → verify output
- [ ] Task 4.1.5: JavaScript Hello World → verify output
- [ ] Task 4.1.6: HTML preview
- [ ] Task 4.1.7: CSS preview

### Slice 4.2: Feature Testing
- [ ] Task 4.2.1: stdin input panel (C++ cin test)
- [ ] Task 4.2.2: STOP button (infinite loop)
- [ ] Task 4.2.3: Timeout (>10s Python sleep)
- [ ] Task 4.2.4: Ctrl+Enter shortcut
- [ ] Task 4.2.5: Save / Save As
- [ ] Task 4.2.6: Open file with language auto-detect
- [ ] Task 4.2.7: Multi-tab: open 3 tabs different languages
- [ ] Task 4.2.8: Find & Replace dialog
- [ ] Task 4.2.9: Settings dialog (change font size)
- [ ] Task 4.2.10: Compiler error display

---

## Notes

- xcb-cursor library was missing. Alternative: use `QT_QPA_PLATFORM=wayland` on this GNOME/Wayland session
- Java requires sudo for install — user confirmed they'll install manually
- All compiler tests (non-GUI) pass: 10/10
- ncode command verified working in PATH
