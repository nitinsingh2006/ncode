#!/usr/bin/env bash
# Nitin Editor — setup script
# Creates the virtual environment, installs dependencies, sets up compilers, icons, and desktop shortcuts.

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
    echo "[1/5] Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "      Created: $VENV_DIR"
else
    echo "[1/5] Virtual environment already exists."
fi

# Step 2: Upgrade pip
echo "[2/5] Upgrading pip..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip

# Step 3: Install requirements
echo "[3/5] Installing Python dependencies (PySide6)..."
"$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"

# Step 4: Check & Install Compilers (C/C++, Java, Rust, Node.js)
echo "[4/5] Checking compilers (C++, Java, Rust, Node.js)..."

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
        # Prompt user with a 15-second timeout to avoid hanging in unattended scripts
        if read -r -t 15 -p "      Install them now using sudo apt? [Y/n] " answer; then
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
            sudo apt-get update -qq || true
            sudo apt-get install -y "${MISSING_PKGS[@]}"
            echo "      ✓ Compilers installed successfully."
        else
            echo "      ⚠ apt-get not found. Please install manually: ${MISSING_PKGS[*]}"
        fi
    else
        echo "      ℹ Skipped compiler installation."
        echo "        To install later: sudo apt install -y ${MISSING_PKGS[*]}"
    fi
fi

# Step 5: Install Icons, Desktop Shortcut & CLI command
echo "[5/5] Installing Desktop shortcuts, icon & 'ncode' CLI..."

# Install icons
ICON_DIR_512="$HOME/.local/share/icons/hicolor/512x512/apps"
ICON_DIR_SVG="$HOME/.local/share/icons/hicolor/scalable/apps"
mkdir -p "$ICON_DIR_512" "$ICON_DIR_SVG"

if [[ -f "$SCRIPT_DIR/assets/icon.png" ]]; then
    cp "$SCRIPT_DIR/assets/icon.png" "$ICON_DIR_512/nitin-editor.png"
fi
if [[ -f "$SCRIPT_DIR/assets/icon.svg" ]]; then
    cp "$SCRIPT_DIR/assets/icon.svg" "$ICON_DIR_SVG/nitin-editor.svg"
fi

# Update icon cache if tool exists
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

# Create launcher CLI script in ~/.local/bin/ncode
mkdir -p "$HOME/.local/bin"
cat << EOF > "$HOME/.local/bin/ncode"
#!/usr/bin/env bash
exec "$SCRIPT_DIR/run.sh" "\$@"
EOF
chmod +x "$HOME/.local/bin/ncode"

# Create application desktop entry
APP_DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$APP_DESKTOP_DIR"
DESKTOP_FILE="$APP_DESKTOP_DIR/nitin-editor.desktop"

cat << EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Type=Application
Name=Nitin Editor
GenericName=Code Editor
Comment=Private desktop code editor with DSA Practice & AI Chatbot
Exec=$HOME/.local/bin/ncode %F
Icon=nitin-editor
Terminal=false
Categories=Development;IDE;
Keywords=code;editor;python;cpp;java;javascript;dsa;
StartupNotify=true
StartupWMClass=NitinEditor
MimeType=text/x-python;text/x-csrc;text/x-c++src;text/x-java;application/javascript;text/html;text/css;
EOF
chmod +x "$DESKTOP_FILE"

# Copy to Desktop if ~/Desktop directory exists
if [[ -d "$HOME/Desktop" ]]; then
    cp "$DESKTOP_FILE" "$HOME/Desktop/Nitin Editor.desktop"
    chmod +x "$HOME/Desktop/Nitin Editor.desktop"
    if command -v gio >/dev/null 2>&1; then
        gio set "$HOME/Desktop/Nitin Editor.desktop" metadata::trusted true 2>/dev/null || true
    fi
    echo "      ✓ Desktop icon created: ~/Desktop/Nitin Editor.desktop"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DESKTOP_DIR" 2>/dev/null || true
fi

echo ""
echo "======================================================"
echo "  Setup Complete! ✨"
echo "======================================================"
echo "• Desktop app icon: Ready on your Desktop & Application Menu"
echo "• Terminal command: Type 'ncode' anywhere"
echo "• Launcher script:  $SCRIPT_DIR/run.sh"
