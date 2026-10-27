#!/usr/bin/env bash
# Nitin Editor — launcher script
# Usage: run.sh [optional_file]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
MAIN_PY="$SCRIPT_DIR/app/main.py"

# Auto-setup on first run if venv is missing
if [[ ! -f "$VENV_DIR/bin/activate" ]]; then
    echo "======================================================"
    echo "  [ncode] First run detected! Setting up environment..."
    echo "======================================================"
    bash "$SCRIPT_DIR/setup.sh" --all
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Wayland / X11 auto-detection
if [[ -n "${WAYLAND_DISPLAY:-}" || "${XDG_SESSION_TYPE:-}" == "wayland" ]]; then
    export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-wayland}"
else
    export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
fi
export QTWEBENGINE_CHROMIUM_FLAGS="${QTWEBENGINE_CHROMIUM_FLAGS:---no-sandbox}"

exec python3 "$MAIN_PY" "$@"
