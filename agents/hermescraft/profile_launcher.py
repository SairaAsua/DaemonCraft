#!/usr/bin/env python3

"""
HermesCraft — Embodied Hermes agents for Minecraft

Copyright (c) 2026 bigph00t

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

"""
HermesCraft Profile Launcher

Creates a Hermes profile for a Minecraft agent and launches both:
1. Mineflayer bot server (HTTP API on unique port)
2. Hermes agent bound to that profile

Usage:
    python profile_launcher.py <agent_name> [options]
    python profile_launcher.py Steve --mc-username Steve --model kimi/kimi-k2.6

The launcher:
- Creates a Hermes profile if it doesn't exist
- Enables the 'minecraft' toolset in profile config
- Copies SOUL-minecraft.md as the profile's SOUL
- Starts bot/server.js with unique port/username
- Starts Hermes agent with the profile
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Add hermes-agent to path so we can import its internals
HERMES_AGENT_DIR = Path.home() / ".hermes" / "hermes-agent"
sys.path.insert(0, str(HERMES_AGENT_DIR))

from hermes_cli.profiles import create_profile, get_profile_dir, profile_exists


# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

# DaemonCraft agents directory layout:
#   DaemonCraft/
#     agents/
#       hermescraft/     <- this file
#       bot/             <- Mineflayer bot server
#       SOUL-minecraft.md
AGENTS_DIR = Path(__file__).parent.parent.resolve()
BOT_DIR = AGENTS_DIR / "bot"
SOUL_FILE = AGENTS_DIR / "SOUL-minecraft.md"
PROMPTS_DIR = AGENTS_DIR / "prompts"

DEFAULT_MC_HOST = "localhost"
DEFAULT_MC_PORT = 25565
DEFAULT_BOT_API_PORT = 3001


def log(msg: str):
    print(f"[⭑ HermesCraft] {msg}")


def error(msg: str):
    print(f"[❌ HermesCraft] {msg}", file=sys.stderr)
    sys.exit(1)


def get_template_profile(template_name: str) -> str:
    """Resolve a template name to a Hermes profile name.
    
    Templates are stored as Hermes profiles named '<template>-template'.
    If the template profile doesn't exist, create it from prompts/ or SOUL-minecraft.md.
    """
    template_profile = f"{template_name}-template"
    
    if profile_exists(template_profile):
        return template_profile
    
    # Try to create template from prompts/
    prompt_file = PROMPTS_DIR / f"{template_name}.md"
    if not prompt_file.exists():
        # Try landfolk subdirectory
        prompt_file = PROMPTS_DIR / template_name / f"{template_name}.md"
    
    if not prompt_file.exists():
        log(f"Template '{template_name}' not found in prompts/, using default SOUL-minecraft.md")
        prompt_file = SOUL_FILE
    
    log(f"Creating template profile: {template_profile} from {prompt_file.name}")
    
    try:
        template_dir = create_profile(
            name=template_profile,
            clone_from="default",
            clone_config=True,
        )
    except Exception as e:
        error(f"Failed to create template profile: {e}")
    
    # Copy the prompt as SOUL.md
    soul_dst = template_dir / "SOUL.md"
    if prompt_file.exists():
        soul_dst.write_text(prompt_file.read_text())
        log(f"Copied {prompt_file.name} as template SOUL.md")
    
    # Enable minecraft toolset
    config_path = template_dir / "config.yaml"
    if config_path.exists():
        import yaml
        try:
            config = yaml.safe_load(config_path.read_text()) or {}
            # toolsets
            toolsets = config.get("toolsets", ["hermes-cli"])
            if isinstance(toolsets, list) and "minecraft" not in toolsets:
                toolsets.append("minecraft")
                config["toolsets"] = toolsets
            # platform_toolsets.cli
            platform_toolsets = config.get("platform_toolsets", {})
            cli_toolsets = platform_toolsets.get("cli", [])
            if isinstance(cli_toolsets, list) and "minecraft" not in cli_toolsets:
                cli_toolsets.append("minecraft")
                platform_toolsets["cli"] = cli_toolsets
                config["platform_toolsets"] = platform_toolsets
            config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))
        except Exception:
            pass
    
    return template_profile


# ══════════════════════════════════════════════════════════️═════════════════════════════
# Profile Setup
# ═══════════════════════════════════════════════════════════════════════════════

def setup_profile(
    name: str,
    model: str = None,
    clone_from: str = None,
    template: str = None,
) -> Path:
    """Create or verify a Hermes profile for this Minecraft agent."""

    # Resolve template to clone_from
    if template:
        clone_from = get_template_profile(template)
    elif clone_from is None:
        # Default to cloning from the user's default profile to inherit auth
        clone_from = "default"

    if profile_exists(name):
        log(f"Profile '{name}' already exists — using it.")
        profile_dir = get_profile_dir(name)
    else:
        log(f"Creating Hermes profile: {name} (cloned from {clone_from})")
        try:
            profile_dir = create_profile(
                name=name,
                clone_from=clone_from,
                clone_config=True,
            )
            log(f"Profile created at: {profile_dir}")
        except Exception as e:
            error(f"Failed to create profile: {e}")

    # Ensure profile config enables minecraft toolset
    config_path = profile_dir / "config.yaml"
    config = {}
    if config_path.exists():
        import yaml
        try:
            config = yaml.safe_load(config_path.read_text()) or {}
        except Exception:
            config = {}

    # Update config to enable minecraft toolset
    toolsets = config.get("toolsets", ["hermes-cli"])
    if isinstance(toolsets, list) and "minecraft" not in toolsets:
        toolsets.append("minecraft")
        config["toolsets"] = toolsets
        log("Enabled 'minecraft' toolset in profile config")

    # ALSO add minecraft to platform_toolsets.cli so TUI loads it
    platform_toolsets = config.get("platform_toolsets", {})
    cli_toolsets = platform_toolsets.get("cli", [])
    if isinstance(cli_toolsets, list) and "minecraft" not in cli_toolsets:
        cli_toolsets.append("minecraft")
        platform_toolsets["cli"] = cli_toolsets
        config["platform_toolsets"] = platform_toolsets
        log("Enabled 'minecraft' in platform_toolsets.cli for TUI")

    # Set model only if explicitly provided (otherwise inherit from clone)
    if model:
        config["model"] = model
        log(f"Set model to: {model}")

    import yaml
    config_path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))

    # If using a template, the SOUL is already cloned. Otherwise copy default SOUL.
    soul_dst = profile_dir / "SOUL.md"
    if not template and SOUL_FILE.exists():
        soul_dst.write_text(SOUL_FILE.read_text())
        log(f"Copied {SOUL_FILE.name} to profile SOUL.md")

    # Ensure .env has MC_API_URL for the bot server
    env_path = profile_dir / ".env"
    env_lines = []
    if env_path.exists():
        env_lines = env_path.read_text().splitlines()

    env_vars = {}
    for line in env_lines:
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env_vars[k] = v

    # Add MC_API_URL if not present
    if "MC_API_URL" not in env_vars:
        env_lines.append("")
        env_lines.append("# HermesCraft bot server URL")
        env_lines.append("MC_API_URL=http://localhost:3001")
        env_path.write_text("\n".join(env_lines))
        log("Added MC_API_URL to profile .env")

    # Create shell alias wrapper
    alias_dir = Path.home() / ".local" / "bin"
    alias_dir.mkdir(parents=True, exist_ok=True)
    alias_path = alias_dir / name
    alias_script = f'#!/bin/sh\nexec hermes -p {name} "$@"\n'
    alias_path.write_text(alias_script)
    alias_path.chmod(0o755)
    log(f"Created alias: {name} -> hermes -p {name}")

    return profile_dir


# ══════════════════════════════════════════════════════════️═════════════════════════════
# Bot Server Management
# ═══════════════════════════════════════════════════════════════════════════════

def start_bot_server(
    mc_host: str,
    mc_port: int,
    mc_username: str,
    api_port: int,
) -> subprocess.Popen:
    """Start the Mineflayer bot server as a background process."""
    env = {
        **os.environ,
        "MC_HOST": mc_host,
        "MC_PORT": str(mc_port),
        "MC_USERNAME": mc_username,
        "MC_AUTH": "offline",
        "API_PORT": str(api_port),
    }

    log(f"Starting bot server: {mc_username} @ {mc_host}:{mc_port} (API port {api_port})")
    proc = subprocess.Popen(
        ["node", "server.js"],
        cwd=str(BOT_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # Wait for server to be ready
    for i in range(30):
        time.sleep(1)
        if proc.poll() is not None:
            output = proc.stdout.read().decode("utf-8", errors="replace") if proc.stdout else ""
            error(f"Bot server exited early:\n{output[-1000:]}")

        # Check if API is up
        import urllib.request
        try:
            urllib.request.urlopen(f"http://localhost:{api_port}/status", timeout=2)
            log(f"Bot server ready on port {api_port}")
            return proc
        except Exception:
            pass

    error("Bot server failed to start within 30 seconds")


# ══════════════════════════════════════════════════════════️═════════════════════════════
# Hermes Agent Launch
# ═══════════════════════════════════════════════════════════════════════════════

def start_hermes_agent(
    profile_name: str,
    mode: str = "chat",
) -> subprocess.Popen:
    """Start Hermes with the given profile."""
    log(f"Starting Hermes agent with profile: {profile_name} (mode: {mode})")

    cmd = ["hermes", "-p", profile_name, mode]
    proc = subprocess.Popen(
        cmd,
        env={**os.environ, "MC_API_URL": f"http://localhost:{DEFAULT_BOT_API_PORT}"},
    )
    log(f"Hermes agent started (PID: {proc.pid})")
    return proc


# ══════════════════════════════════════════════════════════️═════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Launch a Minecraft agent as a Hermes profile"
    )
    parser.add_argument("name", help="Agent/profile name (e.g., Steve)")
    parser.add_argument("--mc-username", help="Minecraft username for the bot")
    parser.add_argument("--mc-host", default=DEFAULT_MC_HOST, help="Minecraft server host")
    parser.add_argument("--mc-port", type=int, default=DEFAULT_MC_PORT, help="Minecraft server port")
    parser.add_argument("--api-port", type=int, default=DEFAULT_BOT_API_PORT, help="Bot HTTP API port")
    parser.add_argument("--model", help="LLM model for the agent")
    parser.add_argument("--clone-from", help="Clone profile config from existing profile")
    parser.add_argument("--template", help="Use a prompt template (e.g., goblin, pirate, monk). Looks for prompts/<template>.md")
    parser.add_argument("--mode", default="chat", choices=["chat", "gateway"], help="Hermes mode")
    parser.add_argument("--skip-bot", action="store_true", help="Skip starting the bot server (assume external)")
    parser.add_argument("--setup-only", action="store_true", help="Only create profile, don't launch agent")

    args = parser.parse_args()

    mc_username = args.mc_username or args.name
    # Profile names must be lowercase alphanumeric with hyphens/underscores
    profile_name = args.name.lower().replace(" ", "-")
    api_port = args.api_port

    log(f"HermesCraft Profile Launcher")
    log(f"Agent: {args.name} | Profile: {profile_name} | MC User: {mc_username} | Server: {args.mc_host}:{args.mc_port}")

    # Step 1: Setup profile
    profile_dir = setup_profile(
        name=profile_name,
        model=args.model,
        clone_from=args.clone_from,
        template=args.template,
    )

    if args.setup_only:
        log(f"Profile setup complete. Run again without --setup-only to launch.")
        sys.exit(0)

    # Step 2: Start bot server
    bot_proc = None
    if not args.skip_bot:
        bot_proc = start_bot_server(
            mc_host=args.mc_host,
            mc_port=args.mc_port,
            mc_username=mc_username,
            api_port=api_port,
        )

    # Step 3: Start Hermes agent
    hermes_env = {**os.environ}
    if bot_proc:
        hermes_env["MC_API_URL"] = f"http://localhost:{api_port}"

    log(f"Starting Hermes: hermes -p {profile_name} {args.mode}")
    try:
        hermes_proc = subprocess.run(
            ["hermes", "-p", profile_name, args.mode],
            env=hermes_env,
        )
    except KeyboardInterrupt:
        log("Interrupted by user")
    finally:
        if bot_proc:
            log("Stopping bot server...")
            bot_proc.terminate()
            try:
                bot_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                bot_proc.kill()

    log("Shutdown complete")


if __name__ == "__main__":
    main()
