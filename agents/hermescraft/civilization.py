#!/usr/bin/env python3
"""
DaemonCraft Civilization Mode Launcher

Launch multiple persistent Minecraft agents that interact socially.
Each agent gets their own Mineflayer bot (unique username) and Hermes profile
(unique personality + shared civilization rules).

Usage:
    python civilization.py start          # Launch all agents
    python civilization.py status         # Check agent/bot health
    python civilization.py logs <name>    # Tail logs for an agent
    python civilization.py stop           # Stop all agents and bots
    python civilization.py stop <name>    # Stop a specific agent

Each agent runs as two background processes:
  - Bot server: node server.js (HTTP API for Minecraft control)
  - Hermes agent: hermes -p <profile> chat (LLM reasoning)
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Add parent dir to path to import profile_launcher
SCRIPT_DIR = Path(__file__).parent.resolve()
AGENTS_DIR = SCRIPT_DIR.parent.resolve()
BOT_DIR = AGENTS_DIR / "bot"
SOUL_CIV = AGENTS_DIR / "SOUL-civilization.md"
PROMPTS_DIR = AGENTS_DIR / "prompts"
RUN_DIR = Path.home() / ".local" / "share" / "daemoncraft" / "civilization"
LOG_DIR = RUN_DIR / "logs"
PID_DIR = RUN_DIR / "pids"

# ═══════════════════════════════════════════════════════════════════════════════
# Cast Configuration
# ═══════════════════════════════════════════════════════════════════════════════

# Start small: 2 characters to test multi-agent interaction
# Expand by adding more entries here.
DEFAULT_CAST = [
    {"name": "Marcus", "port": 3001, "template": "marcus"},
    {"name": "Sarah",  "port": 3002, "template": "sarah"},
]

MC_HOST = "localhost"
MC_PORT = 25565


def log(msg: str):
    print(f"[Civ] {msg}")


def error(msg: str):
    print(f"[Civ ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def ensure_dirs():
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    PID_DIR.mkdir(parents=True, exist_ok=True)


def pid_file(name: str, kind: str) -> Path:
    return PID_DIR / f"{name}_{kind}.pid"


def log_file(name: str, kind: str) -> Path:
    return LOG_DIR / f"{name}_{kind}.log"


def read_pid(name: str, kind: str) -> int | None:
    pf = pid_file(name, kind)
    if pf.exists():
        try:
            return int(pf.read_text().strip())
        except ValueError:
            return None
    return None


def write_pid(name: str, kind: str, pid: int):
    pid_file(name, kind).write_text(str(pid))


def remove_pid(name: str, kind: str):
    pid_file(name, kind).unlink(missing_ok=True)


def is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# Profile Setup
# ═══════════════════════════════════════════════════════════════════════════════

def setup_civilization_profile(name: str, template: str, port: int) -> Path:
    """Create or update a Hermes profile for a civilization agent."""
    profile_name = name.lower().replace(" ", "-")

    # Ensure hermes-agent is importable
    hermes_agent_dir = Path.home() / ".hermes" / "hermes-agent"
    if str(hermes_agent_dir) not in sys.path:
        sys.path.insert(0, str(hermes_agent_dir))

    from profile_launcher import setup_profile, SOUL_FILE, PROMPTS_DIR

    # Use setup-only to create/update the profile
    profile_dir = setup_profile(
        name=profile_name,
        clone_from="default",
        template=template,
    )

    # Build the composite SOUL: civilization rules + character personality
    soul_parts = []
    if SOUL_CIV.exists():
        soul_parts.append(SOUL_CIV.read_text())

    # Find the character prompt
    prompt_file = PROMPTS_DIR / f"{template}.md"
    if not prompt_file.exists():
        prompt_file = PROMPTS_DIR / template / f"{template}.md"
    if prompt_file.exists():
        soul_parts.append(f"\n\n---\n\n{prompt_file.read_text()}")

    if soul_parts:
        soul_dst = profile_dir / "SOUL.md"
        soul_dst.write_text("\n".join(soul_parts))
        log(f"Wrote composite SOUL for {name}")

    # Update .env with correct MC_API_URL
    env_path = profile_dir / ".env"
    env_lines = []
    if env_path.exists():
        env_lines = env_path.read_text().splitlines()

    env_vars = {}
    for line in env_lines:
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env_vars[k] = v

    # Replace or add MC_API_URL
    new_lines = [ln for ln in env_lines if not ln.startswith("MC_API_URL=")]
    new_lines.append(f"MC_API_URL=http://localhost:{port}")
    env_path.write_text("\n".join(new_lines) + "\n")

    return profile_dir


# ═══════════════════════════════════════════════════════════════════════════════
# Bot Server Launch
# ═══════════════════════════════════════════════════════════════════════════════

def start_bot(name: str, port: int) -> int:
    """Start the Mineflayer bot server for this agent. Returns PID."""
    log_file_path = log_file(name, "bot")
    out = open(log_file_path, "a")

    env = {
        **os.environ,
        "MC_HOST": MC_HOST,
        "MC_PORT": str(MC_PORT),
        "MC_USERNAME": name,
        "MC_AUTH": "offline",
        "API_PORT": str(port),
    }

    log(f"Starting bot {name} on port {port}...")
    proc = subprocess.Popen(
        ["node", "server.js"],
        cwd=str(BOT_DIR),
        env=env,
        stdout=out,
        stderr=subprocess.STDOUT,
    )
    write_pid(name, "bot", proc.pid)
    log(f"Bot {name} started (PID {proc.pid})")

    # Wait for API to be ready
    import urllib.request
    for i in range(30):
        time.sleep(1)
        if proc.poll() is not None:
            out.close()
            tail = log_file_path.read_text()[-500:]
            error(f"Bot {name} exited early:\n{tail}")
        try:
            urllib.request.urlopen(f"http://localhost:{port}/status", timeout=2)
            log(f"Bot {name} API ready on port {port}")
            break
        except Exception:
            pass
    else:
        out.close()
        error(f"Bot {name} failed to become ready within 30s")

    return proc.pid


# ═══════════════════════════════════════════════════════════════════════════════
# Hermes Agent Launch
# ═══════════════════════════════════════════════════════════════════════════════

def start_agent(name: str, port: int) -> int:
    """Start the Hermes agent for this character (single-turn autonomy). Returns PID."""
    profile_name = name.lower().replace(" ", "-")
    log_file_path = log_file(name, "agent")
    out = open(log_file_path, "a")

    env = {
        **os.environ,
        "MC_API_URL": f"http://localhost:{port}",
    }

    log(f"Starting Hermes agent for {name} (profile: {profile_name})...")
    proc = subprocess.Popen(
        ["hermes", "-p", profile_name, "chat", "-q", "Begin.", "--yolo", "--quiet"],
        env=env,
        stdout=out,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
    )
    write_pid(name, "agent", proc.pid)
    log(f"Agent {name} started (PID {proc.pid})")
    return proc.pid


# ═══════════════════════════════════════════════════════════════════════════════
# Commands
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_start(cast: list[dict]):
    ensure_dirs()
    for member in cast:
        name = member["name"]
        port = member["port"]
        template = member["template"]

        # Skip if already running
        bot_pid = read_pid(name, "bot")
        agent_pid = read_pid(name, "agent")
        if bot_pid and is_alive(bot_pid) and agent_pid and is_alive(agent_pid):
            log(f"{name} is already running (bot PID {bot_pid}, agent PID {agent_pid})")
            continue

        # 1. Setup profile
        setup_civilization_profile(name, template, port)

        # 2. Start bot
        start_bot(name, port)

        # 3. Start agent
        start_agent(name, port)

        time.sleep(2)  # Small delay between agents to avoid resource spikes

    log("Civilization Mode launched.")


def cmd_status(cast: list[dict]):
    print(f"{'Agent':<10} {'Bot PID':<10} {'Bot OK':<8} {'Agent PID':<10} {'Agent OK':<8}")
    print("-" * 55)
    for member in cast:
        name = member["name"]
        bot_pid = read_pid(name, "bot")
        agent_pid = read_pid(name, "agent")
        bot_ok = "yes" if bot_pid and is_alive(bot_pid) else "no"
        agent_ok = "yes" if agent_pid and is_alive(agent_pid) else "no"
        print(f"{name:<10} {str(bot_pid or '-'):<10} {bot_ok:<8} {str(agent_pid or '-'):<10} {agent_ok:<8}")


def cmd_stop(cast: list[dict] | None = None, target_name: str | None = None):
    members = cast or []
    if target_name:
        members = [m for m in members if m["name"].lower() == target_name.lower()]
        if not members:
            error(f"Agent '{target_name}' not found in cast")

    for member in members:
        name = member["name"]
        for kind in ("agent", "bot"):
            pid = read_pid(name, kind)
            if pid and is_alive(pid):
                log(f"Stopping {name} {kind} (PID {pid})...")
                try:
                    os.kill(pid, signal.SIGTERM)
                    # Wait up to 5s
                    for _ in range(50):
                        if not is_alive(pid):
                            break
                        time.sleep(0.1)
                    else:
                        os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            remove_pid(name, kind)
        log(f"{name} stopped.")


def cmd_logs(name: str, kind: str = "agent", follow: bool = False):
    lf = log_file(name, kind)
    if not lf.exists():
        error(f"No logs found for {name} {kind}")
    if follow:
        subprocess.run(["tail", "-f", str(lf)])
    else:
        subprocess.run(["tail", "-n", "50", str(lf)])


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="DaemonCraft Civilization Mode")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("start", help="Launch all civilization agents")
    sub.add_parser("status", help="Check agent health")
    p_stop = sub.add_parser("stop", help="Stop all or one agent")
    p_stop.add_argument("name", nargs="?", help="Specific agent to stop (default: all)")
    p_logs = sub.add_parser("logs", help="Show agent logs")
    p_logs.add_argument("name", help="Agent name")
    p_logs.add_argument("--kind", choices=["agent", "bot"], default="agent")
    p_logs.add_argument("-f", "--follow", action="store_true")

    args = parser.parse_args()

    cast = DEFAULT_CAST

    if args.cmd == "start":
        cmd_start(cast)
    elif args.cmd == "status":
        cmd_status(cast)
    elif args.cmd == "stop":
        # If user passed a name as positional, handle it
        target = getattr(args, "name", None)
        cmd_stop(cast, target_name=target)
    elif args.cmd == "logs":
        cmd_logs(args.name, args.kind, args.follow)


if __name__ == "__main__":
    main()
