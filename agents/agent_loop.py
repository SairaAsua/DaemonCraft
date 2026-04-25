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
import os
import sys
import time
from pathlib import Path

# Ensure Hermes is on path
HERMES_DIR = Path.home() / ".hermes" / "hermes-agent"
if str(HERMES_DIR) not in sys.path:
    sys.path.insert(0, str(HERMES_DIR))

from run_agent import AIAgent


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
    )

    conversation_history = []
    turn_count = 0

    try:
        while True:
            turn_count += 1
            print(f"[loop] Turn {turn_count}")

            # Alternate between initial prompt and a continuation prompt
            prompt = initial_prompt if turn_count == 1 else (
                "Continue your current activity. Check your status, surroundings, "
                "and any pending commands. Act as your character would."
            )

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
                if response:
                    print(f"[loop] Response: {response[:200]}")

            except Exception as e:
                print(f"[loop] Error during turn: {e}")

            print(f"[loop] Sleeping {interval}s...")
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
