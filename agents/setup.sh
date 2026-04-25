#!/usr/bin/env bash
# DaemonCraft Setup Script
# Installs dependencies, creates symlinks, and verifies the environment

set -e

echo "== DaemonCraft Setup =="

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found. Install Node.js 18+ first."
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "ERROR: Node.js 18+ required. Found: $(node -v)"
    exit 1
fi

echo "Node.js: $(node -v)"

# Install bot dependencies
echo "Installing bot dependencies..."
cd "$(dirname "$0")/bot"
npm install

cd ..

# Symlink mc CLI
MC_BIN="$(pwd)/bin/mc"
if [ -f "$MC_BIN" ]; then
    mkdir -p ~/.local/bin
    ln -sf "$MC_BIN" ~/.local/bin/dc-mc
    echo "Linked dc-mc CLI to ~/.local/bin/dc-mc"
    echo "Usage: dc-mc status | dc-mc chat \"hello\" | dc-mc inventory"
else
    echo "WARNING: bin/mc not found. CLI not linked."
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Start a cast: python3 agents/daemoncraft.py start landfolk"
echo "  2. Or start civilization: python3 agents/daemoncraft.py start civilization"
echo "  3. Check status: python3 agents/daemoncraft.py status landfolk"
