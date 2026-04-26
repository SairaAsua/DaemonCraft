#!/usr/bin/env python3
"""
Hermes-native persistent agent loop for Minecraft bots.

Instead of spawning `hermes chat` repeatedly (high overhead, 60s gaps),
this script creates a single AIAgent instance and calls run_conversation()
in a loop with a configurable interval.

Usage:
    python agent_loop.py --profile stevie --prompt "Begin."

This uses Hermes' AIAgent directly — the same class used by the CLI,
gateway, and batch runner. We do NOT reinvent the tool-calling loop.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

# Ensure Hermes is on path
HERMES_DIR = Path.home() / ".hermes" / "hermes-agent"
if str(HERMES_DIR) not in sys.path:
    sys.path.insert(0, str(HERMES_DIR))

from run_agent import AIAgent


MC_API_URL = os.getenv("MC_API_URL", "http://localhost:3001")


def fetch_plan() -> dict:
    """Fetch the bot's current plan from the bot server."""
    try:
        with urllib.request.urlopen(f"{MC_API_URL}/plan", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("data", {})
    except Exception:
        return {}


def format_plan(plan: dict) -> str:
    """Format the plan as a string to inject into the prompt."""
    if not plan or not plan.get("goal"):
        return ""
    goal = plan.get("goal", "")
    tasks = plan.get("tasks", [])
    done = sum(1 for t in tasks if t.get("status") == "done")
    total = len(tasks)

    # Plan fully complete — prompt for next steps
    if total > 0 and done == total:
        return (
            f"Your goal '{goal}' is COMPLETE. All {total} tasks finished.\n"
            f"Announce your success to the player with mc_chat, then EITHER:\n"
            f"  1. Ask what they'd like you to work on next\n"
            f"  2. Set your own goal based on what would be useful (check status, inventory, surroundings)\n"
            f"If you choose option 2, use mc_plan(action='set_goal', goal='...', tasks=[...]) to commit.\n"
        )

    lines = [
        f"Your current goal: {goal}",
        f"Task progress: {done}/{total} done",
    ]
    for i, t in enumerate(tasks):
        sym = {
            "done": "[x]",
            "in_progress": "[->]",
            "blocked": "[!]",
        }.get(t.get("status", ""), "[ ]")
        desc = t.get("description", "")
        att = f" (attempt {t.get('attempts', 0)})" if t.get("attempts") else ""
        lines.append(f"  {sym} {i + 1}. {desc}{att}")
    return "\n".join(lines)


def load_profile_config(profile_name: str) -> dict:
    """Load config from a Hermes profile directory."""
    from hermes_cli.profiles import get_profile_dir, profile_exists

    if not profile_exists(profile_name):
        raise ValueError(f"Profile '{profile_name}' does not exist")

    profile_dir = get_profile_dir(profile_name)
    config_path = profile_dir / "config.yaml"

    config = {}
    if config_path.exists():
        import yaml
        config = yaml.safe_load(config_path.read_text()) or {}

    return config, profile_dir


def build_system_prompt(profile_dir: Path) -> str:
    """Build system prompt from SOUL.md and other context files."""
    parts = []

    soul = profile_dir / "SOUL.md"
    if soul.exists():
        parts.append(soul.read_text())

    # Add other context files if present
    for name in ("AGENTS.md", ".cursorrules"):
        f = profile_dir / name
        if f.exists():
            parts.append(f.read_text())

    return "\n\n".join(parts) if parts else None


def run_agent_loop(profile_name: str, initial_prompt: str, interval: int = 30):
    """Run an AIAgent in a persistent loop."""
    config, profile_dir = load_profile_config(profile_name)

    # Resolve model
    model_cfg = config.get("model", {})
    if isinstance(model_cfg, dict):
        model = model_cfg.get("default", "")
    else:
        model = str(model_cfg)

    # Resolve provider / base_url from provider config
    provider = None
    base_url = None
    providers = config.get("providers", {})
    if providers and isinstance(providers, dict):
        # Use first configured provider
        first_key = next(iter(providers))
        pcfg = providers[first_key]
        if isinstance(pcfg, dict):
            provider = pcfg.get("provider") or first_key
            base_url = pcfg.get("base_url")

    # Resolve toolsets
    toolsets = config.get("toolsets", [])
    if not toolsets:
        toolsets = config.get("platform_toolsets", {}).get("cli", [])

    system_prompt = build_system_prompt(profile_dir)

    # Ensure MC_API_URL is set for the minecraft tools
    mc_api_url = os.getenv("MC_API_URL", "")

    print(f"[loop] Starting persistent agent: {profile_name}")
    print(f"[loop] Model: {model}")
    print(f"[loop] Toolsets: {toolsets}")
    print(f"[loop] MC_API_URL: {mc_api_url}")
    print(f"[loop] Interval: {interval}s")

    agent = AIAgent(
        model=model,
        provider=provider,
        base_url=base_url,
        enabled_toolsets=toolsets,
        ephemeral_system_prompt=system_prompt,
        platform="cli",
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=False,
        reasoning_config={"enabled": False},
        max_iterations=5,
    )

    conversation_history = []
    turn_count = 0

    def log_agent_turn(turn_data: dict):
        """Send turn data to bot server for dashboard display."""
        payload = json.dumps(turn_data).encode("utf-8")
        req = urllib.request.Request(
            f"{MC_API_URL}/agent/log",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                pass
        except Exception:
            pass

    try:
        while True:
            turn_count += 1
            print(f"[loop] Turn {turn_count}", flush=True)

            # Fetch current plan and inject into prompt
            plan = fetch_plan()
            plan_context = format_plan(plan)

            if turn_count == 1:
                prompt = initial_prompt
            else:
                prompt = (
                    "Continue your current activity. Check your status, surroundings, "
                    "and any pending commands. Act as your character would."
                )

            if plan_context:
                prompt = f"{plan_context}\n\n{prompt}"

            turn_log = {
                "turn": turn_count,
                "time": int(time.time() * 1000),
                "prompt": prompt,
                "response": "",
                "tool_calls": [],
                "error": None,
            }

            try:
                result = agent.run_conversation(
                    user_message=prompt,
                    conversation_history=conversation_history,
                )

                # Keep the conversation history for context continuity
                conversation_history = result.get("messages", [])

                # Trim history to avoid token bloat (keep last 20 messages)
                if len(conversation_history) > 20:
                    conversation_history = conversation_history[-20:]

                response = result.get("final_response", "")
                turn_log["response"] = response

                # Extract tool calls from conversation history
                for msg in conversation_history:
                    if msg.get("role") == "assistant" and msg.get("tool_calls"):
                        for tc in msg["tool_calls"]:
                            turn_log["tool_calls"].append({
                                "name": tc.get("function", {}).get("name", "unknown"),
                                "args": tc.get("function", {}).get("arguments", ""),
                            })

                if response:
                    print(f"[loop] Response: {response[:200]}", flush=True)

            except Exception as e:
                turn_log["error"] = str(e)
                print(f"[loop] Error during turn: {e}", flush=True)

            log_agent_turn(turn_log)

            print(f"[loop] Sleeping {interval}s...", flush=True)
            time.sleep(interval)

    except KeyboardInterrupt:
        print("[loop] Interrupted. Exiting.")


def main():
    parser = argparse.ArgumentParser(description="Hermes-native persistent agent loop")
    parser.add_argument("--profile", required=True, help="Hermes profile name")
    parser.add_argument("--prompt", default="Begin.", help="Initial prompt")
    parser.add_argument("--interval", type=int, default=30, help="Seconds between turns")
    args = parser.parse_args()

    run_agent_loop(args.profile, args.prompt, args.interval)


if __name__ == "__main__":
    main()
