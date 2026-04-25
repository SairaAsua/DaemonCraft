#!/usr/bin/env python3
"""Task 11: Test Hermes profile creation for agents."""

import sys
import tempfile
from pathlib import Path

AGENTS_DIR = Path(__file__).parent.parent / "agents"
sys.path.insert(0, str(AGENTS_DIR))

# Mock hermes-cli imports
sys.modules["hermes_cli"] = type(sys)("hermes_cli")
sys.modules["hermes_cli.profiles"] = type(sys)("hermes_cli.profiles")

PROFILES_DIR = Path(tempfile.mkdtemp()) / "profiles"


def profile_exists(name):
    return (PROFILES_DIR / name).exists()


def get_profile_dir(name):
    return PROFILES_DIR / name


def create_profile(name, clone_from=None, clone_config=False):
    d = PROFILES_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    # Create a minimal config.yaml
    config = {"toolsets": ["hermes-cli"]}
    import yaml
    (d / "config.yaml").write_text(yaml.dump(config))
    return d


sys.modules["hermes_cli.profiles"].profile_exists = profile_exists
sys.modules["hermes_cli.profiles"].get_profile_dir = get_profile_dir
sys.modules["hermes_cli.profiles"].create_profile = create_profile


def test_setup_profile():
    from daemoncraft import setup_agent_profile

    agent = {
        "name": "TestBot",
        "template": "steve",
        "port": 9999,
        "model": "kimi/kimi-k2.6",
    }

    profile_dir = setup_agent_profile("testcast", agent, soul_file=None)

    # Check profile dir exists
    assert profile_dir.exists(), "Profile dir not created"

    # Check config.yaml has minecraft toolset
    import yaml
    config = yaml.safe_load((profile_dir / "config.yaml").read_text())
    assert "minecraft" in config.get("toolsets", []), "minecraft toolset not enabled"

    # Check platform_toolsets.cli has minecraft
    platform = config.get("platform_toolsets", {})
    assert "minecraft" in platform.get("cli", []), "minecraft not in platform_toolsets.cli"

    # Check model set
    assert config.get("model") == {"default": "kimi/kimi-k2.6"}, "model not set"

    # Check .env has MC_API_URL
    env_text = (profile_dir / ".env").read_text()
    assert "MC_API_URL=http://localhost:9999" in env_text, "MC_API_URL not set"

    print("PASS: Profile created with correct config")
    return True


def test_composite_soul():
    from daemoncraft import setup_agent_profile

    # Create a temporary soul file
    soul_file = Path(tempfile.mktemp(suffix=".md"))
    soul_file.write_text("# Base Soul\nBe helpful.")

    agent = {
        "name": "Steve",
        "template": "steve",
        "port": 3001,
    }

    profile_dir = setup_agent_profile("testcast2", agent, soul_file=soul_file)
    soul_path = profile_dir / "SOUL.md"

    assert soul_path.exists(), "SOUL.md not created"
    content = soul_path.read_text()
    assert "Base Soul" in content, "Base soul not in composite"

    print("PASS: Composite SOUL created correctly")
    return True


if __name__ == "__main__":
    ok = True
    ok = test_setup_profile() and ok
    ok = test_composite_soul() and ok
    sys.exit(0 if ok else 1)
