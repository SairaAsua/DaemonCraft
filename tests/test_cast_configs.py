#!/usr/bin/env python3
"""Task 12: Test cast YAML config parsing."""

import sys
from pathlib import Path

AGENTS_DIR = Path(__file__).parent.parent / "agents"
sys.path.insert(0, str(AGENTS_DIR))

# We need to mock hermes imports since they may not be available in CI
sys.modules["hermes_cli"] = type(sys)("hermes_cli")
sys.modules["hermes_cli.profiles"] = type(sys)("hermes_cli.profiles")

def profile_exists(name):
    return False

def get_profile_dir(name):
    return Path.home() / ".hermes" / "profiles" / name

def create_profile(name, clone_from=None, clone_config=False):
    d = get_profile_dir(name)
    d.mkdir(parents=True, exist_ok=True)
    return d

sys.modules["hermes_cli.profiles"].profile_exists = profile_exists
sys.modules["hermes_cli.profiles"].get_profile_dir = get_profile_dir
sys.modules["hermes_cli.profiles"].create_profile = create_profile


def test_load_all_casts():
    from daemoncraft import load_cast

    casts_dir = AGENTS_DIR / "casts"
    cast_files = list(casts_dir.glob("*.yaml"))

    if not cast_files:
        print("FAIL: No cast YAML files found")
        return False

    for cf in cast_files:
        name = cf.stem
        try:
            config = load_cast(name)
        except Exception as e:
            print(f"FAIL: Could not load cast '{name}': {e}")
            return False

        # Validate structure
        assert "agents" in config, f"{name}: missing 'agents' key"
        assert isinstance(config["agents"], list), f"{name}: 'agents' must be a list"
        assert len(config["agents"]) > 0, f"{name}: no agents defined"

        for agent in config["agents"]:
            assert "name" in agent, f"{name}: agent missing 'name'"
            assert "port" in agent, f"{name}: agent {agent.get('name')} missing 'port'"
            assert "template" in agent, f"{name}: agent {agent.get('name')} missing 'template'"

        print(f"PASS: Cast '{name}' loaded ({len(config['agents'])} agents)")

    print(f"PASS: All {len(cast_files)} cast configs valid")
    return True


def test_companion_cast():
    from daemoncraft import load_cast

    config = load_cast("companion")
    assert len(config["agents"]) == 1
    assert config["agents"][0]["name"] == "Steve"
    print("PASS: Companion cast validated")
    return True


def test_civilization_cast():
    from daemoncraft import load_cast

    config = load_cast("civilization")
    assert len(config["agents"]) == 7
    names = {a["name"] for a in config["agents"]}
    assert "Marcus" in names
    assert "Elena" in names
    print("PASS: Civilization cast validated")
    return True


def test_landfolk_cast():
    from daemoncraft import load_cast

    config = load_cast("landfolk")
    assert len(config["agents"]) == 5
    names = {a["name"] for a in config["agents"]}
    assert "Moss" in names
    assert "Flint" in names
    print("PASS: Landfolk cast validated")
    return True


if __name__ == "__main__":
    ok = True
    ok = test_load_all_casts() and ok
    ok = test_companion_cast() and ok
    ok = test_civilization_cast() and ok
    ok = test_landfolk_cast() and ok
    sys.exit(0 if ok else 1)
