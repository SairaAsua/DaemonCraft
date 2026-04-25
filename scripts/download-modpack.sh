#!/usr/bin/env bash
set -euo pipefail

# Manual fallback helper for downloading/installing the Phi-Craft modpack.
# The itzg/minecraft-server image can auto-install from CurseForge if you provide
# a CF_API_KEY. If that fails, use this script to prepare a local modpack zip.
#
# Usage:
#   1. Download the Phi-Craft modpack .zip from CurseForge manually:
#      https://www.curseforge.com/minecraft/modpacks/phi-craft/files/7654543
#   2. Place the downloaded file in server/modpacks/phi-craft.zip
#   3. Uncomment the manual fallback lines in docker-compose.yml
#   4. Run: docker compose up -d minecraft
#
# This script can also verify that the local zip exists.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODPACK_DIR="${SCRIPT_DIR}/../server/modpacks"
MODPACK_ZIP="${MODPACK_DIR}/phi-craft.zip"

echo "=== DaemonCraft Modpack Fallback Helper ==="
echo ""

if [[ -f "$MODPACK_ZIP" ]]; then
    echo "Found local modpack zip: $MODPACK_ZIP"
    echo "Size: $(du -h "$MODPACK_ZIP" | cut -f1)"
    echo ""
    echo "To use it, ensure the manual fallback is uncommented in docker-compose.yml"
    echo "and then run: docker compose up -d minecraft"
    exit 0
else
    echo "Local modpack zip NOT found at: $MODPACK_ZIP"
    echo ""
    echo "Please download the Phi-Craft modpack manually:"
    echo "  1. Visit https://www.curseforge.com/minecraft/modpacks/phi-craft/files/7654543"
    echo "  2. Download the server or client .zip file (server pack is preferred)."
    echo "  3. Save it as: server/modpacks/phi-craft.zip"
    echo ""
    echo "Alternatively, set CF_API_KEY in a .env file and use automatic install:"
    echo "  cp .env.example .env   # then edit with your API key"
    echo "  docker compose up -d minecraft"
    exit 1
fi
