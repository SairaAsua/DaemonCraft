#!/usr/bin/env python3
"""
Blueprint Engine for DaemonCraft
Handles init execution, entity tagging, block tracking, and cleanup.

Usage:
    python3 scripts/blueprint-engine.py init agents/blueprints/el-codigo-que-suena.json
    python3 scripts/blueprint-engine.py cleanup agents/blueprints/el-codigo-que-suena.json
"""

import json
import re
import subprocess
import sys
from pathlib import Path

BLUEPRINTS_DIR = Path(__file__).parent.parent / "agents" / "blueprints"
DATA_DIR = Path(__file__).parent.parent / "agents" / "data"


def mc_cmd(cmd: str):
    """Send command to Minecraft server console."""
    subprocess.run(
        ["docker", "exec", "--user", "1000", "daemoncraft-minecraft", "mc-send-to-console", cmd],
        capture_output=True, text=True
    )


def extract_tag(blueprint: dict) -> str:
    """Generate a safe tag name from blueprint metadata."""
    title = blueprint.get("metadata", {}).get("title", "unknown")
    return re.sub(r'[^a-z0-9_]', '_', title.lower())


def inject_summon_tags(commands: list[str], tag: str) -> list[str]:
    """Inject blueprint tags into all /summon commands."""
    result = []
    for cmd in commands:
        stripped = cmd.strip()
        if not stripped:
            result.append(cmd)
            continue

        parts = stripped.split()
        cmd_name = parts[0].lstrip("/") if parts else ""

        if cmd_name == "summon":
            if "{" in stripped:
                modified = stripped.replace("{", f'{{Tags:["{tag}"],', 1)
                result.append(modified)
            else:
                result.append(f'{stripped} {{Tags:["{tag}"]}}')
        else:
            result.append(cmd)
    return result


def extract_block_ops(commands: list[str]) -> list[dict]:
    """Extract setblock and fill operations from commands."""
    ops = []
    for cmd in commands:
        stripped = cmd.strip()
        if not stripped:
            continue

        parts = stripped.split()
        if len(parts) < 2:
            continue

        cmd_name = parts[0].lstrip("/")

        if cmd_name == "setblock" and len(parts) >= 5:
            ops.append({
                "type": "setblock",
                "x": int(parts[1]),
                "y": int(parts[2]),
                "z": int(parts[3])
            })
        elif cmd_name == "fill" and len(parts) >= 8:
            ops.append({
                "type": "fill",
                "x1": int(parts[1]),
                "y1": int(parts[2]),
                "z1": int(parts[3]),
                "x2": int(parts[4]),
                "y2": int(parts[5]),
                "z2": int(parts[6])
            })
    return ops


def collect_all_commands(blueprint: dict) -> list[str]:
    """Collect all commands from init and all phases."""
    commands = []

    init = blueprint.get("init", {})
    commands.extend(init.get("commands", []))

    for phase in blueprint.get("phases", []):
        for event in phase.get("events", []):
            if event.get("type") == "command":
                commands.append(event["command"])

    return commands


def extract_entity_types(commands: list[str]) -> list[str]:
    """Extract entity types from summon commands."""
    types = set()
    for cmd in commands:
        stripped = cmd.strip()
        if "summon" in stripped:
            parts = stripped.split()
            if len(parts) >= 2:
                entity = parts[1]
                if entity.startswith("minecraft:"):
                    entity = entity[10:]
                types.add(entity)
    return sorted(list(types))


def run_init(blueprint_path: Path):
    """Execute init phase of a blueprint with tagging and tracking."""
    with open(blueprint_path) as f:
        blueprint = json.load(f)

    tag = extract_tag(blueprint)
    print(f"[engine] Running init for blueprint: {tag}")

    all_commands = collect_all_commands(blueprint)
    block_ops = extract_block_ops(all_commands)
    entity_types = extract_entity_types(all_commands)

    print(f"[engine] Tracked {len(block_ops)} block operations")
    print(f"[engine] Tracked entity types: {entity_types}")

    init_commands = blueprint.get("init", {}).get("commands", [])
    tagged_commands = inject_summon_tags(init_commands, tag)

    for cmd in tagged_commands:
        print(f"[engine] EXEC: {cmd[:100]}")
        mc_cmd(cmd)

    sensors = blueprint.get("init", {}).get("sensors", [])
    for sensor in sensors:
        name = sensor["name"]
        criterion = sensor["criterion"]
        mc_cmd(f"/scoreboard objectives add {name} {criterion}")
        print(f"[engine] SENSOR: {name} ({criterion})")

    tracking = {
        "tag": tag,
        "blueprint_path": str(blueprint_path),
        "block_ops": block_ops,
        "entity_types": entity_types,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tracking_file = DATA_DIR / f"blueprint-tracking-{tag}.json"
    with open(tracking_file, "w") as f:
        json.dump(tracking, f, indent=2)

    print(f"[engine] Init complete. Tracking saved to {tracking_file}")
    return tracking


def run_cleanup(blueprint_path: Path):
    """Remove all blueprint-tagged entities and tracked blocks."""
    with open(blueprint_path) as f:
        blueprint = json.load(f)

    tag = extract_tag(blueprint)
    print(f"[engine] Running cleanup for blueprint: {tag}")

    mc_cmd(f"/kill @e[tag={tag}]")
    print(f"[engine] Killed entities with tag: {tag}")

    tracking_file = DATA_DIR / f"blueprint-tracking-{tag}.json"
    if tracking_file.exists():
        with open(tracking_file) as f:
            tracking = json.load(f)

        for op in tracking.get("block_ops", []):
            if op["type"] == "setblock":
                mc_cmd(f"/setblock {op['x']} {op['y']} {op['z']} air")
                print(f"[engine] CLEAR setblock: {op['x']},{op['y']},{op['z']}")
            elif op["type"] == "fill":
                mc_cmd(f"/fill {op['x1']} {op['y1']} {op['z1']} {op['x2']} {op['y2']} {op['z2']} air")
                print(f"[engine] CLEAR fill: {op['x1']},{op['y1']},{op['z1']} → {op['x2']},{op['y2']},{op['z2']}")

        tracking_file.unlink()
        print(f"[engine] Removed tracking file")
    else:
        print(f"[engine] No tracking file found for {tag}")

    sensors = blueprint.get("init", {}).get("sensors", [])
    for sensor in sensors:
        name = sensor["name"]
        mc_cmd(f"/scoreboard objectives remove {name}")
        print(f"[engine] Removed sensor: {name}")

    print(f"[engine] Cleanup complete for {tag}")


def resolve_blueprint_path(name_or_path: str) -> Path:
    """Resolve a blueprint name or path to an absolute Path."""
    path = Path(name_or_path)
    if path.exists():
        return path

    path = BLUEPRINTS_DIR / name_or_path
    if path.exists():
        return path

    if not str(name_or_path).endswith(".json"):
        path = BLUEPRINTS_DIR / f"{name_or_path}.json"
        if path.exists():
            return path

    print(f"[engine] Blueprint not found: {name_or_path}")
    sys.exit(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Blueprint Engine")
    parser.add_argument("action", choices=["init", "cleanup"], help="Action to perform")
    parser.add_argument("blueprint", help="Path to blueprint JSON or name")
    args = parser.parse_args()

    path = resolve_blueprint_path(args.blueprint)

    if args.action == "init":
        run_init(path)
    else:
        run_cleanup(path)
