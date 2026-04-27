#!/usr/bin/env python3
"""
Hermes-native persistent agent loop for Minecraft bots.

Event-driven: chat messages arrive via WebSocket and trigger turns immediately.
Idle heartbeat runs every 30s when no chat activity.

Usage:
    python agent_loop.py --profile stevie --prompt "Begin."
"""

import argparse
import json
import os
import sys
import threading
import time
import urllib.request
from pathlib import Path

# Ensure Hermes is on path
HERMES_DIR = Path.home() / ".hermes" / "hermes-agent"
if str(HERMES_DIR) not in sys.path:
    sys.path.insert(0, str(HERMES_DIR))

from run_agent import AIAgent

MC_API_URL = os.getenv("MC_API_URL", "http://localhost:3001")
BOT_USERNAME = os.getenv("MC_USERNAME", "Steve").lower()


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level helpers (safe to call from threads)
# ═══════════════════════════════════════════════════════════════════════════════

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


def send_heartbeat(next_turn_in: float | None = None, turn_in_progress: bool = False):
    """Send heartbeat countdown to bot server for dashboard display."""
    payload = json.dumps({
        "nextTurnIn": next_turn_in,
        "turnInProgress": turn_in_progress,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{MC_API_URL}/agent/heartbeat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            pass
    except Exception:
        pass


def _safe_trim_history(messages: list, max_msgs: int = 20) -> list:
    """Trim conversation history without breaking tool_call chains.

    If a tool result message is kept, its parent assistant message (containing
    the matching tool_call) must also be kept. Otherwise tool_call_id refs
    become orphaned and the API rejects with 400.
    """
    if len(messages) <= max_msgs:
        return messages

    keep_from = len(messages) - max_msgs

    # Collect all tool_call_ids from tool messages inside the proposed window
    tool_ids_in_window = set()
    for msg in messages[keep_from:]:
        if msg.get("role") == "tool" and msg.get("tool_call_id"):
            tool_ids_in_window.add(msg["tool_call_id"])

    # Ensure every assistant that owns those tool_calls is also in the window
    for i, msg in enumerate(messages):
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                tc_id = tc.get("id")
                if tc_id and tc_id in tool_ids_in_window:
                    keep_from = min(keep_from, i)

    return messages[keep_from:]


# ═══════════════════════════════════════════════════════════════════════════════
# Plan helpers
# ═══════════════════════════════════════════════════════════════════════════════

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

    for name in ("AGENTS.md", ".cursorrules"):
        f = profile_dir / name
        if f.exists():
            parts.append(f.read_text())

    return "\n\n".join(parts) if parts else None


# ═══════════════════════════════════════════════════════════════════════════════
# WebSocket chat trigger
# ═══════════════════════════════════════════════════════════════════════════════

chat_event = threading.Event()
pending_messages = []
message_lock = threading.Lock()
last_chat_time = int(time.time() * 1000)
ws_connected = threading.Event()
turn_in_progress = threading.Event()
current_agent = None
next_turn_time = None
countdown_lock = threading.Lock()
cancel_event = threading.Event()


def _wire_tool_cancel_event(event) -> bool:
    """Find the minecraft_tools module (loaded by Hermes) and wire the cancel event."""
    for mod_name in ("tools.minecraft_tools", "minecraft_tools", "hermescraft.minecraft_tools"):
        mod = sys.modules.get(mod_name)
        if mod and hasattr(mod, "set_cancel_event"):
            mod.set_cancel_event(event)
            print(f"[loop] Wired cancel event into {mod_name}", flush=True)
            return True
    return False


def _ws_on_message(ws, message):
    global last_chat_time, pending_messages, chat_event
    try:
        data = json.loads(message)
        msg_type = data.get("type")
        if msg_type == "chat":
            msgs = data.get("data", [])
            new_msgs = [
                m for m in msgs
                if m.get("time", 0) > last_chat_time
                and m.get("from", "").lower() != BOT_USERNAME
            ]
            if new_msgs:
                with message_lock:
                    pending_messages.extend(new_msgs)
                    last_chat_time = max(m.get("time", 0) for m in new_msgs)
                chat_event.set()
                if turn_in_progress.is_set() and current_agent is not None:
                    try:
                        cancel_event.set()
                        current_agent._interrupt_requested = True
                        print("[ws] Chat arrived during turn — interrupting to respond now", flush=True)
                    except Exception:
                        pass
        elif msg_type == "status":
            pass
        else:
            pass
    except Exception as e:
        print(f"[ws] Error: {e}", flush=True)


def _ws_on_open(ws):
    ws_connected.set()
    print("[ws] Connected to bot WebSocket", flush=True)


def _ws_on_close(ws, close_status_code, close_msg):
    ws_connected.clear()
    print(f"[ws] Disconnected: {close_status_code} {close_msg}", flush=True)


def _ws_listener():
    import websocket
    ws_url = MC_API_URL.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
    while True:
        try:
            ws = websocket.WebSocketApp(
                ws_url,
                on_message=_ws_on_message,
                on_open=_ws_on_open,
                on_close=_ws_on_close,
            )
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"[ws] Connection error: {e}. Retrying in 5s...", flush=True)
        ws_connected.clear()
        time.sleep(5)


def start_ws_listener():
    t = threading.Thread(target=_ws_listener, daemon=True)
    t.start()
    ws_connected.wait(timeout=5)


# ═══════════════════════════════════════════════════════════════════════════════
# Countdown timer
# ═══════════════════════════════════════════════════════════════════════════════

def _countdown_timer(interval: int):
    print("[loop] Countdown timer started", flush=True)
    while True:
        try:
            time.sleep(5)
            with countdown_lock:
                target = next_turn_time
            in_progress = turn_in_progress.is_set()
            if target is None:
                if in_progress:
                    send_heartbeat(next_turn_in=None, turn_in_progress=True)
                else:
                    send_heartbeat(next_turn_in=None, turn_in_progress=False)
                continue
            remaining = target - time.time()
            if remaining > 0 and not in_progress:
                print(f"[loop] Next turn in {int(remaining)}s...", flush=True)
                send_heartbeat(next_turn_in=remaining, turn_in_progress=False)
            elif in_progress:
                send_heartbeat(next_turn_in=None, turn_in_progress=True)
            else:
                print("[loop] Turn starting now...", flush=True)
                send_heartbeat(next_turn_in=0, turn_in_progress=False)
        except Exception as e:
            print(f"[loop] Countdown thread error: {e}", flush=True)
            time.sleep(5)


def start_countdown(interval: int):
    t = threading.Thread(target=_countdown_timer, args=(interval,), daemon=True)
    t.start()


# ═══════════════════════════════════════════════════════════════════════════════
# Main loop
# ═══════════════════════════════════════════════════════════════════════════════

def run_agent_loop(profile_name: str, initial_prompt: str, interval: int = 30):
    """Run an AIAgent in a persistent event-driven loop."""
    config, profile_dir = load_profile_config(profile_name)

    model_cfg = config.get("model", {})
    if isinstance(model_cfg, dict):
        model = model_cfg.get("default", "")
    else:
        model = str(model_cfg)

    provider = None
    base_url = None
    providers = config.get("providers", {})
    if providers and isinstance(providers, dict):
        first_key = next(iter(providers))
        pcfg = providers[first_key]
        if isinstance(pcfg, dict):
            provider = pcfg.get("provider") or first_key
            base_url = pcfg.get("base_url")

    toolsets = config.get("toolsets", [])
    if not toolsets:
        toolsets = config.get("platform_toolsets", {}).get("cli", [])

    system_prompt = build_system_prompt(profile_dir)
    mc_api_url = os.getenv("MC_API_URL", "")

    print(f"[loop] Starting persistent agent: {profile_name}")
    print(f"[loop] Model: {model}")
    print(f"[loop] Provider: {provider}")
    print(f"[loop] Base URL: {base_url}")
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
        max_iterations=8,
    )

    global current_agent
    current_agent = agent

    global next_turn_time

    conversation_history = []
    turn_count = 0
    _cancel_wired = False

    start_ws_listener()
    start_countdown(interval)

    try:
        while True:
            turn_count += 1
            print(f"[loop] Turn {turn_count}", flush=True)

            # Wire cancel event into tools (Hermes loads modules lazily; retry until found)
            if not _cancel_wired:
                if _wire_tool_cancel_event(cancel_event):
                    _cancel_wired = True

            with countdown_lock:
                next_turn_time = time.time() + interval

            triggered = chat_event.wait(timeout=interval)
            chat_event.clear()

            msgs = []
            if triggered:
                with message_lock:
                    msgs = list(pending_messages)
                    pending_messages.clear()
                if msgs:
                    senders = ", ".join({m.get("from", "Player") for m in msgs})
                    print(f"[loop] Chat trigger from {senders}", flush=True)
                    with countdown_lock:
                        next_turn_time = None

            is_chat_triggered = bool(msgs)

            plan = fetch_plan()
            plan_context = format_plan(plan)

            if msgs:
                chat_lines = "\n".join([
                    f"- {m.get('from', 'Player')}: {m.get('message', '')}"
                    for m in msgs
                ])
                prompt = (
                    f"New chat messages — respond immediately:\n{chat_lines}\n\n"
                    f"If this is a new task or request from the player, handle it right away. "
                    f"Remember: if the player gives you a NEW task that replaces your current work, "
                    f"FIRST call mc_plan(action='clear_goal') to wipe the old plan, "
                    f"THEN create a new plan with mc_plan(action='set_goal', ...)."
                )
            elif turn_count == 1:
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

            agent._interrupt_requested = False
            cancel_event.clear()
            turn_in_progress.set()
            send_heartbeat(next_turn_in=None, turn_in_progress=True)
            try:
                result = agent.run_conversation(
                    user_message=prompt,
                    conversation_history=conversation_history,
                )

                conversation_history = result.get("messages", [])
                conversation_history = _safe_trim_history(conversation_history, max_msgs=20)

                response = result.get("final_response", "")
                turn_log["response"] = response

                is_budget_error = (
                    "maximum iterations" in (response or "")
                    or "couldn't summarize" in (response or "")
                    or "tool_call_id" in (response or "")
                )

                mc_chat_used = False
                for msg in conversation_history:
                    if msg.get("role") == "assistant" and msg.get("tool_calls"):
                        for tc in msg["tool_calls"]:
                            name = tc.get("function", {}).get("name", "")
                            turn_log["tool_calls"].append({
                                "name": name,
                                "args": tc.get("function", {}).get("arguments", ""),
                            })
                            if name == "mc_chat":
                                mc_chat_used = True

                if is_budget_error:
                    print("[loop] Budget exhausted — tools executed but summary failed. Will retry next turn.", flush=True)
                    conversation_history = []
                elif response and not mc_chat_used and is_chat_triggered:
                    chat_msg = response.strip()
                    if len(chat_msg) > 300:
                        chat_msg = chat_msg[:297] + "..."
                    try:
                        payload = json.dumps({"message": chat_msg}).encode("utf-8")
                        req = urllib.request.Request(
                            f"{MC_API_URL}/chat/send",
                            data=payload,
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        )
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            pass
                        print(f"[loop] Auto-sent to chat: {chat_msg[:80]}...", flush=True)
                    except Exception as e:
                        print(f"[loop] Auto-chat failed: {e}", flush=True)

                if response and not is_budget_error:
                    print(f"[loop] Response: {response[:200]}", flush=True)

            except Exception as e:
                turn_log["error"] = str(e)
                print(f"[loop] Error during turn: {e}", flush=True)
            finally:
                turn_in_progress.clear()
                send_heartbeat(next_turn_in=None, turn_in_progress=False)

            log_agent_turn(turn_log)

    except KeyboardInterrupt:
        print("[loop] Interrupted. Exiting.")


def main():
    parser = argparse.ArgumentParser(description="Hermes-native persistent agent loop")
    parser.add_argument("--profile", required=True, help="Hermes profile name")
    parser.add_argument("--prompt", default="Begin.", help="Initial prompt")
    parser.add_argument("--interval", type=int, default=30, help="Seconds between idle turns")
    args = parser.parse_args()

    run_agent_loop(args.profile, args.prompt, args.interval)


if __name__ == "__main__":
    main()
