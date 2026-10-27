#!/usr/bin/env bash
# Nitin Editor — setup script
# Creates the virtual environment, installs dependencies, and optionally installs compilers.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

INSTALL_COMPILERS=false
if [[ "${1:-}" == "--compilers" || "${1:-}" == "-y" || "${1:-}" == "--all" ]]; then
    INSTALL_COMPILERS=true
fi

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
echo "[3/4] Installing Python dependencies (PySide6)..."
"$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"

# Step 4: Check & Install Compilers (C/C++, Java, Rust, Node.js)
echo "[4/4] Checking compilers (C++, Java, Rust, Node.js)..."

MISSING_PKGS=()

if ! command -v g++ >/dev/null 2>&1; then
    MISSING_PKGS+=(build-essential g++)
fi
if ! command -v javac >/dev/null 2>&1; then
    MISSING_PKGS+=(default-jdk)
fi
if ! command -v rustc >/dev/null 2>&1; then
    MISSING_PKGS+=(rustc)
fi
if ! command -v node >/dev/null 2>&1; then
    MISSING_PKGS+=(nodejs)
fi

if [[ ${#MISSING_PKGS[@]} -eq 0 ]]; then
    echo "      ✓ All common compilers (g++, javac, rustc, node) are already installed!"
else
    echo "      Missing packages: ${MISSING_PKGS[*]}"
    
    DO_INSTALL=false
    if [[ "$INSTALL_COMPILERS" == "true" ]]; then
        DO_INSTALL=true
    elif [[ -t 0 ]]; then
        # Prompt user with a 20-second timeout to avoid hanging in unattended scripts
        if read -r -t 20 -p "      Install them now using sudo apt? [Y/n] " answer; then
            answer="${answer:-Y}"
            if [[ "$answer" =~ ^[Yy]$ ]]; then
                DO_INSTALL=true
            fi
        else
            echo ""
            echo "      (Timed out waiting for input, skipping compiler installation)"
        fi
    fi

    if [[ "$DO_INSTALL" == "true" ]]; then
        if command -v apt-get >/dev/null 2>&1; then
            echo "      Installing via apt..."
            sudo apt-get update -qq
            sudo apt-get install -y "${MISSING_PKGS[@]}"
            echo "      ✓ Compilers installed successfully."
        else
            echo "      ⚠ apt-get not found. Please install manually on your distro: ${MISSING_PKGS[*]}"
        fi
    else
        echo "      ℹ Skipped compiler installation."
        echo "        To install later: sudo apt install -y ${MISSING_PKGS[*]}"
    fi
fi

echo ""
echo "======================================================"
echo "  Setup Complete! ✨"
echo "======================================================"
echo "Launch with: $SCRIPT_DIR/run.sh"
echo "Or:          ./run.sh"
