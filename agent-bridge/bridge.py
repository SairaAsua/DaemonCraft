#!/usr/bin/env python3
"""
DaemonCraft Agent Bridge

A Flask HTTP server that receives triggers from external systems
(e.g., Hermes CLI) and forwards commands to Mineflayer bot HTTP APIs.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional

import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
TRIGGER_TIMEOUT = int(os.getenv("TRIGGER_TIMEOUT", "30"))
MAX_CONCURRENT_TRIGGERS = int(os.getenv("MAX_CONCURRENT_TRIGGERS", "10"))

# Parse BOT_REGISTRY: name=http://host:port,name2=http://host2:port2
BOT_REGISTRY: Dict[str, str] = {}
_registry_raw = os.getenv("BOT_REGISTRY", "")
if _registry_raw:
    for entry in _registry_raw.split(","):
        if "=" in entry:
            name, url = entry.split("=", 1)
            BOT_REGISTRY[name.strip()] = url.strip()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("agent-bridge")

# ---------------------------------------------------------------------------
# Flask App
# ---------------------------------------------------------------------------
app = Flask(__name__)


def bot_health(name: str, url: str) -> dict:
    """Check health of a single bot."""
    try:
        resp = requests.get(f"{url}/health", timeout=5)
        return {"name": name, "url": url, "status": resp.json()}
    except requests.RequestException as e:
        return {"name": name, "url": url, "status": "unreachable", "error": str(e)}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    """Bridge health check."""
    return jsonify({"status": "ok", "registered_daemons": list(BOT_REGISTRY.keys())})


@app.route("/daemons", methods=["GET"])
def list_daemons():
    """List all configured daemons and their current status."""
    daemons = [bot_health(name, url) for name, url in BOT_REGISTRY.items()]
    return jsonify({"daemons": daemons})


@app.route("/trigger", methods=["POST"])
def trigger():
    """
    Receive a trigger and forward it to the appropriate bot.

    Body: {
        "daemon": "DaemonBot",      # target daemon name (must match registry)
        "action": "chat",           # action type
        "params": {                 # action-specific parameters
            "message": "Hello world"
        }
    }
    """
    data = request.get_json(force=True, silent=True) or {}

    daemon_name = data.get("daemon")
    action = data.get("action")
    params = data.get("params", {})

    if not daemon_name or not action:
        return jsonify({"error": "Missing required fields: daemon, action"}), 400

    bot_url = BOT_REGISTRY.get(daemon_name)
    if not bot_url:
        return jsonify({"error": f"Daemon '{daemon_name}' not found in registry"}), 404

    logger.info(f"Trigger: daemon={daemon_name} action={action} params={params}")

    # Map actions to bot API endpoints
    try:
        if action == "chat":
            message = params.get("message", "")
            resp = requests.post(
                f"{bot_url}/chat",
                json={"message": message},
                timeout=TRIGGER_TIMEOUT,
            )

        elif action == "command":
            command = params.get("command")
            cmd_params = params.get("params", {})
            resp = requests.post(
                f"{bot_url}/command",
                json={"command": command, "params": cmd_params},
                timeout=TRIGGER_TIMEOUT,
            )

        elif action == "state":
            resp = requests.get(f"{bot_url}/state", timeout=TRIGGER_TIMEOUT)

        elif action == "inventory":
            resp = requests.get(f"{bot_url}/inventory", timeout=TRIGGER_TIMEOUT)

        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400

        resp.raise_for_status()
        return jsonify({
            "success": True,
            "daemon": daemon_name,
            "action": action,
            "result": resp.json(),
        })

    except requests.RequestException as e:
        logger.error(f"Failed to reach bot {daemon_name}: {e}")
        return jsonify({
            "success": False,
            "daemon": daemon_name,
            "action": action,
            "error": str(e),
        }), 502


@app.route("/broadcast", methods=["POST"])
def broadcast():
    """
    Send a chat message to ALL registered daemons.

    Body: {"message": "Hello all daemons"}
    """
    data = request.get_json(force=True, silent=True) or {}
    message = data.get("message", "")

    if not message:
        return jsonify({"error": "Missing 'message' field"}), 400

    results = []
    for name, url in BOT_REGISTRY.items():
        try:
            resp = requests.post(
                f"{url}/chat",
                json={"message": message},
                timeout=TRIGGER_TIMEOUT,
            )
            results.append({"daemon": name, "status": resp.status_code})
        except requests.RequestException as e:
            results.append({"daemon": name, "error": str(e)})

    return jsonify({"success": True, "message": message, "results": results})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("DaemonCraft Agent Bridge")
    logger.info(f"Registered daemons: {list(BOT_REGISTRY.keys())}")
    logger.info("=" * 50)
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
