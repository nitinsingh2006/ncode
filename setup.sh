#!/usr/bin/env bash
# Nitin Editor — setup script
# Creates the virtual environment and installs all dependencies.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "======================================================"
echo "  Nitin Editor — Setup"
echo "======================================================"
echo ""

# Step 1: Create virtual environment
if [[ ! -d "$VENV_DIR" ]]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "      Created: $VENV_DIR"
else
    echo "[1/4] Virtual environment already exists."
fi

# Step 2: Upgrade pip
echo "[2/4] Upgrading pip..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip

# Step 3: Install requirements
echo "[3/4] Installing Python dependencies..."
"$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"

echo "[4/4] Setup complete."
echo ""
echo "Launch with: $SCRIPT_DIR/run.sh"
echo "Or:          ncode"
