"""
Training data logger for DaemonCraft agent loops.

Captures every conversation turn as a structured JSONL record.
These records become the training dataset for fine-tuning a local model
to internalize tool knowledge and bot behavior.

Usage (in agent_loop.py):
    from training.logger import TurnLogger
    logger = TurnLogger(profile_name)
    logger.log_turn(prompt, conversation_history, response_text, error)
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_training_data_dir() -> Path:
    """Return the directory for training data JSONL files."""
    d = Path.home() / ".local" / "share" / "daemoncraft" / "training_data"
    d.mkdir(parents=True, exist_ok=True)
    return d


class TurnLogger:
    """Logs each agent turn to a JSONL file for later fine-tuning."""

    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.log_path = get_training_data_dir() / f"{profile_name}.jsonl"
        self.turn_count = 0

    def log_turn(
        self,
        prompt: str,
        conversation_history: List[Dict[str, Any]],
        response_text: Optional[str] = None,
        error: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        """Log a single turn to JSONL.

        Args:
            prompt: The user prompt sent this turn.
            conversation_history: Full message list after the turn (includes assistant + tool results).
            response_text: The assistant's final response string (if any).
            error: Error message if the turn failed entirely.
            system_prompt: The system prompt the agent was using (for dataset completeness).
        """
        self.turn_count += 1

        # Extract tool calls and results from the conversation history
        tool_calls = []
        for msg in conversation_history:
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    tool_calls.append({
                        "name": tc.get("function", {}).get("name"),
                        "arguments": tc.get("function", {}).get("arguments", {}),
                    })
            elif msg.get("role") == "tool":
                tool_calls.append({
                    "role": "tool",
                    "name": msg.get("name"),
                    "content_preview": str(msg.get("content", ""))[:500],
                })

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "profile": self.profile_name,
            "turn": self.turn_count,
            "prompt": prompt,
            "system_prompt": system_prompt,
            "conversation_history": conversation_history,
            "response_text": response_text,
            "tool_calls": tool_calls,
            "error": error,
        }

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        except Exception as e:
            # Never crash the agent loop because of logging
            print(f"[training_logger] Write failed: {e}")

    def stats(self) -> Dict[str, Any]:
        """Return basic stats about the logged data."""
        count = 0
        if self.log_path.exists():
            with open(self.log_path, "r", encoding="utf-8") as f:
                count = sum(1 for _ in f)
        return {
            "profile": self.profile_name,
            "log_file": str(self.log_path),
            "total_turns_logged": count,
        }
