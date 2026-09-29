# Ralph Loop — Nitin Editor Task Queue

## Status: ACTIVE
## Iteration: 0 / 15
## Max Fix Attempts: 3
## Human Approval Required: sudo package installs

---

## PENDING

- [ ] Fix Qt xcb-cursor missing library (libxcb-cursor0 needed — requires sudo)
- [ ] Try Wayland launch mode as fallback
- [ ] Verify app GUI launches successfully
- [ ] Install openjdk-21-jdk for Java support (requires sudo)
- [ ] Run full language test suite in running app
- [ ] Verify Ctrl+Enter shortcut works
- [ ] Verify STOP button terminates infinite loops
- [ ] Verify HTML preview renders
- [ ] Verify stdin input panel works
- [ ] Verify Save/SaveAs/Open file operations
- [ ] Verify multi-tab support
- [ ] Verify compiler error display
- [ ] Verify Settings dialog saves preferences

## IN_PROGRESS
(none — waiting for sudo operations)

## BLOCKED
- libxcb-cursor0 install — needs sudo password from user
- openjdk-21-jdk install — needs sudo password from user

## COMPLETED
- [x] Create ~/ncode/ project structure
- [x] Generate application icon (PNG)
- [x] Create app/settings.py
- [x] Create app/compiler.py (all 7 languages)
- [x] Create app/runner.py (background thread)
- [x] Create app/editor.py (custom PySide6 editor with syntax highlighting)
- [x] Create app/preview.py (HTML/CSS preview)
- [x] Create app/main.py (main window, 1600+ lines)
- [x] Create app/ui/settings_dialog.py
- [x] Create run.sh, setup.sh, requirements.txt
- [x] Create tests/test_compiler.py
- [x] Create tests/test_languages.sh
- [x] Create .venv with PySide6 6.11.2
- [x] Create ~/.local/bin/ncode command
- [x] Create .desktop launcher
- [x] Create Desktop shortcut
- [x] Run compiler tests: 10/10 PASS (Java skipped)
- [x] Run language shell tests: 9/9 PASS (Java skipped)
- [x] Verify Python, C, C++, JS, stdin, timeout, error detection all work
- [x] Verify ncode command accessible in PATH

---

## Next Actions Requiring Human Sudo

To unblock the PENDING queue, run in your terminal:

```bash
# Fix Qt xcb-cursor (allows X11 mode)
sudo apt-get install -y libxcb-cursor0

# Install Java
sudo apt-get install -y openjdk-21-jdk
```

Then run:
```bash
ncode
```

---

## Iteration Log

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Initial setup | ✅ | All files created |
| 2 | Compiler tests | ✅ | 10/10 pass |
| 3 | Language shell tests | ✅ | 9/9 pass (Java skip) |
| 4 | Qt platform fix | ⏳ | Needs sudo for libxcb-cursor0 |
