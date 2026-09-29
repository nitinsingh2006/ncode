#!/usr/bin/env bash
# Nitin Editor — launcher script
# Usage: run.sh [optional_file]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
MAIN_PY="$SCRIPT_DIR/app/main.py"

# Activate venv
if [[ -f "$VENV_DIR/bin/activate" ]]; then
    source "$VENV_DIR/bin/activate"
else
    echo "[ncode] Virtual environment not found. Please run setup."
    echo "       Expected: $VENV_DIR"
    exit 1
fi

# Wayland/X11 compatibility
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
export QTWEBENGINE_CHROMIUM_FLAGS="${QTWEBENGINE_CHROMIUM_FLAGS:---no-sandbox}"

exec python3 "$MAIN_PY" "$@"
