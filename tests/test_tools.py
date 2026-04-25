#!/usr/bin/env python3
"""Task 10: Test that all 9 consolidated tools are registered."""

import sys
from pathlib import Path

AGENTS_DIR = Path(__file__).parent.parent / "agents"
sys.path.insert(0, str(AGENTS_DIR / "hermescraft"))

# Mock tools.registry before importing minecraft_tools
class MockRegistry:
    def __init__(self):
        self._tools = {}
    def __call__(self, fn):
        self._tools[fn.__name__] = fn
        return fn
    def keys(self):
        return self._tools.keys()
    def items(self):
        return self._tools.items()
    def __getitem__(self, key):
        return self._tools[key]
    def register(self, name, handler=None, fn=None, **kwargs):
        self._tools[name] = handler or fn
    def get(self, name):
        return self._tools.get(name)

mock_registry = MockRegistry()

sys.modules["tools"] = type(sys)("tools")
sys.modules["tools.registry"] = type(sys)("tools.registry")
sys.modules["tools.registry"].registry = mock_registry
sys.modules["tools.registry"].tool_error = Exception

from minecraft_tools import registry

def test_tools_registered():

    expected_tools = {
        "mc_perceive",
        "mc_move",
        "mc_mine",
        "mc_build",
        "mc_craft",
        "mc_combat",
        "mc_chat",
        "mc_manage",
        "mc_screenshot",
    }

    registered = set(registry.keys())
    missing = expected_tools - registered
    extra = registered - expected_tools

    if missing:
        print(f"FAIL: Missing tools: {missing}")
        return False
    if extra:
        print(f"WARN: Extra tools: {extra}")

    print(f"PASS: All {len(expected_tools)} tools registered")
    return True


def test_tool_signatures():
    """Verify key tools have proper docstrings / descriptions."""
def test_tool_signatures():
    """Verify key tools have handlers registered."""
    for name, tool in registry.items():
        if tool is None:
            print(f"FAIL: {name} has no handler")
            return False

    print("PASS: All tools have handlers")
    return True


if __name__ == "__main__":
    ok = True
    ok = test_tools_registered() and ok
    ok = test_tool_signatures() and ok
    sys.exit(0 if ok else 1)
