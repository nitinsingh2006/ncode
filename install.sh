#!/usr/bin/env bash
# Nitin Editor — 1-Line Universal Installer
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/nitinsingh2006/ncode/main/install.sh | bash

set -euo pipefail

REPO_URL="https://github.com/nitinsingh2006/ncode.git"
INSTALL_DIR="${NCODE_DIR:-$HOME/ncode}"

echo "======================================================"
echo "      🚀 Installing ncode (Nitin Editor)             "
echo "======================================================"
echo ""

# Ensure git is installed
if ! command -v git >/dev/null 2>&1; then
    echo "▶ Git is required. Installing git..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq && sudo apt-get install -y git
    else
        echo "❌ Git not found. Please install git and re-run."
        exit 1
    fi
fi

# Clone or pull repository
if [[ -d "$INSTALL_DIR/.git" ]]; then
    echo "▶ Updating existing repository at $INSTALL_DIR..."
    git -C "$INSTALL_DIR" pull --ff-only || true
else
    echo "▶ Cloning ncode repository into $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Run setup with auto-compilers and desktop shortcut creation
echo "▶ Setting up environment and desktop launcher..."
bash "$INSTALL_DIR/setup.sh" --all

echo ""
echo "======================================================"
echo "  🎉 Installation Finished Successfully!             "
echo "======================================================"
echo "• Desktop Icon: Look on your Desktop or App Menu for 'Nitin Editor'"
echo "• CLI Command:  Type 'ncode' in any terminal"
echo "• Direct Path:  $INSTALL_DIR/run.sh"
echo "======================================================"
