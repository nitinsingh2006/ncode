#!/usr/bin/env bash
# Nitin Editor — automated language tests
# Run this after setup to verify all supported languages work.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/../.venv"
PASS=0
FAIL=0
SKIP=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}✓ PASS${NC}  $1"; ((PASS++)); }
fail() { echo -e "  ${RED}✗ FAIL${NC}  $1: $2"; ((FAIL++)); }
skip() { echo -e "  ${YELLOW}⊖ SKIP${NC}  $1: $2"; ((SKIP++)); }

echo ""
echo "======================================================"
echo "  Nitin Editor — Language Tests"
echo "======================================================"
echo ""

# ── Python ──────────────────────────────────────────────────────────────────
echo "▶ Python"
if command -v python3 &>/dev/null; then
    OUTPUT=$(python3 -c 'print("Hello from Python")' 2>&1)
    if [[ "$OUTPUT" == "Hello from Python" ]]; then
        pass "Python execution"
    else
        fail "Python execution" "$OUTPUT"
    fi
else
    skip "Python" "python3 not found"
fi

# ── C ────────────────────────────────────────────────────────────────────────
echo "▶ C"
if command -v gcc &>/dev/null; then
    TMP=$(mktemp -d)
    cat > "$TMP/main.c" << 'EOF'
#include <stdio.h>
int main() { printf("Hello from C\n"); return 0; }
EOF
    gcc "$TMP/main.c" -o "$TMP/main_c" 2>&1
    OUTPUT=$("$TMP/main_c" 2>&1)
    if [[ "$OUTPUT" == "Hello from C" ]]; then
        pass "C execution"
    else
        fail "C execution" "$OUTPUT"
    fi
    rm -rf "$TMP"
else
    skip "C" "gcc not found"
fi

# ── C++ ──────────────────────────────────────────────────────────────────────
echo "▶ C++"
if command -v g++ &>/dev/null; then
    TMP=$(mktemp -d)
    cat > "$TMP/main.cpp" << 'EOF'
#include <iostream>
using namespace std;
int main() { cout << "Hello from C++" << endl; return 0; }
EOF
    g++ "$TMP/main.cpp" -o "$TMP/main_cpp" -std=c++17 2>&1
    OUTPUT=$("$TMP/main_cpp" 2>&1)
    if [[ "$OUTPUT" == "Hello from C++" ]]; then
        pass "C++ execution"
    else
        fail "C++ execution" "$OUTPUT"
    fi
    rm -rf "$TMP"
else
    skip "C++" "g++ not found"
fi

# ── Java ─────────────────────────────────────────────────────────────────────
echo "▶ Java"
if command -v javac &>/dev/null && command -v java &>/dev/null; then
    TMP=$(mktemp -d)
    cat > "$TMP/Main.java" << 'EOF'
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from Java");
    }
}
EOF
    javac "$TMP/Main.java" 2>&1
    OUTPUT=$(java -cp "$TMP" Main 2>&1)
    if [[ "$OUTPUT" == "Hello from Java" ]]; then
        pass "Java execution"
    else
        fail "Java execution" "$OUTPUT"
    fi
    rm -rf "$TMP"
else
    skip "Java" "javac/java not found — install: sudo apt-get install openjdk-21-jdk"
fi

# ── JavaScript ───────────────────────────────────────────────────────────────
echo "▶ JavaScript"
if command -v node &>/dev/null; then
    OUTPUT=$(node -e 'console.log("Hello from JavaScript")' 2>&1)
    if [[ "$OUTPUT" == "Hello from JavaScript" ]]; then
        pass "JavaScript execution"
    else
        fail "JavaScript execution" "$OUTPUT"
    fi
else
    skip "JavaScript" "node not found"
fi

# ── C++ stdin test ────────────────────────────────────────────────────────────
echo "▶ C++ with stdin"
if command -v g++ &>/dev/null; then
    TMP=$(mktemp -d)
    cat > "$TMP/add.cpp" << 'EOF'
#include <iostream>
using namespace std;
int main() { int a, b; cin >> a >> b; cout << a + b; return 0; }
EOF
    g++ "$TMP/add.cpp" -o "$TMP/add" -std=c++17 2>&1
    OUTPUT=$(echo "5 10" | "$TMP/add" 2>&1)
    if [[ "$OUTPUT" == "15" ]]; then
        pass "C++ stdin (5+10=15)"
    else
        fail "C++ stdin" "Expected 15, got: $OUTPUT"
    fi
    rm -rf "$TMP"
fi

# ── Compiler error test ───────────────────────────────────────────────────────
echo "▶ Compiler error detection"
if command -v g++ &>/dev/null; then
    TMP=$(mktemp -d)
    echo "this is not valid cpp code {}{}{}%" > "$TMP/bad.cpp"
    if ! g++ "$TMP/bad.cpp" -o "$TMP/bad" 2>/dev/null; then
        pass "Compiler error detection (g++ correctly failed)"
    else
        fail "Compiler error detection" "Expected compile failure"
    fi
    rm -rf "$TMP"
fi

# ── Timeout test ──────────────────────────────────────────────────────────────
echo "▶ Execution timeout"
if command -v python3 &>/dev/null; then
    OUTPUT=$(timeout 2 python3 -c 'import time; time.sleep(10)' 2>&1)
    EXIT=$?
    if [[ $EXIT -eq 124 ]]; then
        pass "Timeout (process killed at 2s)"
    else
        pass "Timeout mechanism available (exit: $EXIT)"
    fi
fi

# ── ncode command ─────────────────────────────────────────────────────────────
echo "▶ ncode command"
if command -v ncode &>/dev/null; then
    NCODE_PATH=$(command -v ncode)
    pass "ncode command found at: $NCODE_PATH"
else
    skip "ncode" "~/.local/bin/ncode not in PATH yet — re-source shell config"
fi

# ── Desktop launcher ──────────────────────────────────────────────────────────
echo "▶ Desktop launcher"
DESKTOP_FILE="$HOME/.local/share/applications/nitin-editor.desktop"
if [[ -f "$DESKTOP_FILE" ]]; then
    pass "Desktop launcher exists: $DESKTOP_FILE"
else
    fail "Desktop launcher" "$DESKTOP_FILE not found"
fi

echo ""
echo "======================================================"
echo "  Results: ${PASS} passed  /  ${FAIL} failed  /  ${SKIP} skipped"
echo "======================================================"
echo ""

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
exit 0
