#!/usr/bin/env python3
"""
Convert DaemonCraft JSONL training logs into a HuggingFace dataset
for Qwen function-calling fine-tuning.

Usage:
    python convert_dataset.py ~/.local/share/daemoncraft/training_data/steve.jsonl

Outputs:
    ./minecraft_ft_dataset/  (HuggingFace datasets format)
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def extract_chat_messages(record: Dict[str, Any]) -> List[Dict[str, str]]:
    """Convert a logged turn into a chat-style message list."""
    messages = []

    # System prompt with full tool knowledge (this is what we train ON)
    system = record.get("system_prompt") or "You are a Minecraft bot."
    messages.append({"role": "system", "content": system})

    # User prompt
    messages.append({"role": "user", "content": record.get("prompt", "")})

    # Build assistant response from conversation history
    history = record.get("conversation_history", [])
    for msg in history:
        role = msg.get("role", "")
        if role == "assistant":
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                # Append tool calls as JSON blocks so the model learns structured output
                tc_block = "\n".join(
                    f'<tool>{json.dumps({"name": tc.get("function", {}).get("name"), "arguments": tc.get("function", {}).get("arguments", {})})}</tool>'
                    for tc in tool_calls
                )
                content = f"{content}\n{tc_block}".strip()
            messages.append({"role": "assistant", "content": content})
        elif role == "tool":
            # Tool results become assistant context (or we skip them)
            # For function-calling training, tool results are usually separate messages
            content = msg.get("content", "")
            # Truncate very long tool results (e.g. full status JSON)
            if len(content) > 2000:
                content = content[:2000] + "\n... [truncated]"
            messages.append({"role": "tool", "content": content})

    return messages


def filter_valid_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep only turns that produced actual tool calls (the interesting ones)."""
    valid = []
    for r in records:
        # Skip turns with hard errors
        if r.get("error"):
            continue
        # Skip turns with no tool calls (boring idle turns)
        history = r.get("conversation_history", [])
        has_tool_call = any(
            msg.get("role") == "assistant" and msg.get("tool_calls")
            for msg in history
        )
        if has_tool_call:
            valid.append(r)
    return valid


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path_to.jsonl>")
        sys.exit(1)

    jsonl_path = Path(sys.argv[1])
    if not jsonl_path.exists():
        print(f"File not found: {jsonl_path}")
        sys.exit(1)

    print(f"Reading {jsonl_path}...")
    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    print(f"Total records: {len(records)}")
    records = filter_valid_records(records)
    print(f"Valid records (with tool calls, no errors): {len(records)}")

    if len(records) == 0:
        print("No valid training examples found.")
        sys.exit(0)

    # Build HuggingFace-style dataset
    dataset = {"conversations": []}
    for r in records:
        messages = extract_chat_messages(r)
        dataset["conversations"].append(messages)

    # Save as JSONL for easy loading with datasets library
    out_dir = Path("minecraft_ft_dataset")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "train.jsonl"

    with open(out_file, "w", encoding="utf-8") as f:
        for conv in dataset["conversations"]:
            f.write(json.dumps({"messages": conv}, ensure_ascii=False) + "\n")

    print(f"Wrote {len(dataset['conversations'])} examples to {out_file}")
    print(f"\nNext step: run finetune_qwen.py on a machine with a GPU (RTX 3090 or better).")


if __name__ == "__main__":
    main()
