#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════════════
# DaemonCraft Setup — One command to install everything
#
# Usage:
#   ./setup.sh               # full setup
#   ./setup.sh --check       # just verify prerequisites
# ════════════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BOT_DIR="$SCRIPT_DIR/bot"
BIN_DIR="$SCRIPT_DIR/bin"
CHECK_ONLY=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --check) CHECK_ONLY=true; shift ;;
        --help|-h)
            echo "DaemonCraft Setup"
            echo ""
            echo "Usage: ./setup.sh [--check]"
            echo ""
            echo "Installs bot dependencies, mc CLI, and verifies Hermes."
            echo "  --check   Just verify prerequisites, don't install"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

cat << 'BANNER'

  ╔═════════════════════════════════════════════════════════╗
  ║                                               ║
  ║     ⚡ D A E M O N C R A F T ⚡              ║
  ║     AI Agents Living in Minecraft             ║
  ║                                               ║
  ╚═════════════════════════════════════════════════════════╝

BANNER

ERRORS=0

# ── Step 1: Prerequisites ─────────────────────────────────────────────────────
echo "  [1/4] Checking prerequisites..."

# Node.js
if command -v node &>/dev/null; then
    NODE_VER=$(node --version)
    NODE_MAJOR=$(echo "$NODE_VER" | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_MAJOR" -ge 18 ]; then
        echo "    ✓ Node.js $NODE_VER"
    else
        echo "    ✗ Node.js $NODE_VER too old (need ≥18)"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "    ✗ Node.js not found — install from https://nodejs.org/ (v18+)"
    ERRORS=$((ERRORS + 1))
fi

# hermes CLI
HERMES=""
for c in hermes "$HOME/.local/bin/hermes"; do
    if command -v "$c" &>/dev/null; then HERMES="$c"; break; fi
done
if [ -n "$HERMES" ]; then
    echo "    ✓ hermes CLI: $HERMES"
else
    echo "    ✗ hermes CLI not found — pip install hermes-agent"
    ERRORS=$((ERRORS + 1))
fi

# python3 + pyyaml
curl -V &>/dev/null && echo "    ✓ curl" || { echo "    ✗ curl required"; ERRORS=$((ERRORS + 1)); }
python3 --version &>/dev/null && echo "    ✓ python3" || { echo "    ✗ python3 required"; ERRORS=$((ERRORS + 1)); }
if python3 -c "import yaml" 2>/dev/null; then
    echo "    ✓ PyYAML"
else
    echo "    ✗ PyYAML missing — pip install pyyaml"
    ERRORS=$((ERRORS + 1))
fi

# Java (for Paper server)
if command -v java &>/dev/null; then
    echo "    ✓ java $(java -version 2>&1 | head -1)"
else
    echo "    ⚠ java not found — needed for Paper server"
fi

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "  ✗ $ERRORS prerequisite(s) missing. Fix and re-run."
    exit 1
fi

[ "$CHECK_ONLY" = true ] && { echo ""; echo "  ✓ All prerequisites met!"; exit 0; }

# ── Step 2: Bot dependencies ───────────────────────────────────────────────────
echo ""
echo "  [2/4] Installing bot server dependencies..."

cd "$BOT_DIR"
if npm install --no-audit --no-fund 2>&1 | tail -3; then
    echo "    ✓ Bot dependencies installed"
else
    echo "    ✗ npm install failed"
    exit 1
fi
cd "$SCRIPT_DIR"

# ── Step 3: mc CLI ─────────────────────────────────────────────────────────────────────
echo ""
echo "  [3/4] Installing mc CLI..."

MC_LINK="$HOME/.local/bin/mc"
mkdir -p "$HOME/.local/bin"

if [ -L "$MC_LINK" ] || [ ! -e "$MC_LINK" ]; then
    ln -sf "$BIN_DIR/mc" "$MC_LINK"
    echo "    ✓ mc CLI → ~/.local/bin/mc"
else
    echo "    ⚠ ~/.local/bin/mc exists (not a symlink). Skipping."
    echo "      Add $BIN_DIR to your PATH instead."
fi

# daemoncraft.py symlink
DC_LINK="$HOME/.local/bin/daemoncraft"
if [ -L "$DC_LINK" ] || [ ! -e "$DC_LINK" ]; then
    ln -sf "$SCRIPT_DIR/daemoncraft.py" "$DC_LINK"
    echo "    ✓ daemoncraft → ~/.local/bin/daemoncraft"
else
    echo "    ⚠ ~/.local/bin/daemoncraft exists. Skipping."
fi

if command -v mc &>/dev/null; then
    echo "    ✓ mc is on PATH"
else
    echo "    ⚠ ~/.local/bin not in PATH. Add to ~/.bashrc:"
    echo "      export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# ── Step 4: Make scripts executable ────────────────────────────────────────────────────
echo ""
echo "  [4/4] Setting permissions..."

chmod +x "$BIN_DIR/mc" "$SCRIPT_DIR/daemoncraft.py" 2>/dev/null || true
chmod +x "$SCRIPT_DIR/hermescraft/minecraft_tools.py" 2>/dev/null || true

echo "    ✓ Scripts executable"

# Create runtime directories
mkdir -p "$HOME/.local/share/daemoncraft"

echo ""
echo "  ════════════════════════════════════════════════════════════════════════════════"
echo "  ✓ SETUP COMPLETE"
echo "  ════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "  SINGLE AGENT (interactive):"
echo "    daemoncraft start companion"
echo ""
echo "  CIVILIZATION (7 autonomous agents):"
echo "    daemoncraft start civilization"
echo ""
echo "  LANDFOLK (5 peaceful settlers):"
echo "    daemoncraft start landfolk"
echo ""
echo "  MANAGE A RUNNING CAST:"
echo "    daemoncraft status companion"
echo "    daemoncraft stop companion"
echo "    daemoncraft logs companion Steve"
echo ""
echo "  Start Minecraft first (server or singleplayer + Open to LAN)."
echo "  Set online-mode=false in server.properties for offline servers."
echo ""
