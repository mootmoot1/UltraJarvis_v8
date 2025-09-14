from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class RuntimeMemory:
    def __init__(
        self, runtime_file: str = "data/memory_runtime.json", max_turns: int = 10
    ):
        self.runtime_file = Path(runtime_file)
        self.max_turns = max_turns
        self.buffer: List[Dict[str, Any]] = []
        self._ensure_runtime_file()

    def _ensure_runtime_file(self):
        self.runtime_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.runtime_file.exists():
            self.runtime_file.write_text("[]", encoding="utf-8")
        self._load_buffer()

    def _load_buffer(self):
        try:
            self.buffer = json.loads(self.runtime_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to load runtime memory: {e}")
            self.buffer = []

    def _save_buffer(self):
        try:
            self.runtime_file.write_text(
                json.dumps(self.buffer, indent=2), encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Failed to save runtime memory: {e}")

    def add_turn(self, user_input: str, assistant_response: str):
        turn = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "user": user_input,
            "assistant": assistant_response,
        }
        self.buffer.append(turn)

        if len(self.buffer) > self.max_turns:
            self.buffer = self.buffer[-self.max_turns :]

        self._save_buffer()

    def get_recent_context(self, turns: int = 5) -> List[Dict[str, Any]]:
        return self.buffer[-turns:] if self.buffer else []

    def summarize_recent_turns(self, turns: int = 10) -> List[str]:
        recent = self.get_recent_context(turns)
        if not recent:
            return []

        summary = []
        for turn in recent[-3:]:
            user_text = turn.get("user", "")[:100]
            if "goal" in user_text.lower():
                summary.append(f"Goal mentioned: {user_text}")
            elif any(
                cmd in user_text.lower() for cmd in ["run", "seed", "status", "health"]
            ):
                summary.append(f"Command: {user_text}")
            elif "note" in user_text.lower():
                summary.append(f"Note: {user_text}")

        return summary[:3]

    def clear_session(self):
        self.buffer = []
        self._save_buffer()


_runtime_memory: RuntimeMemory = None


def get_runtime_memory() -> RuntimeMemory:
    global _runtime_memory
    if _runtime_memory is None:
        _runtime_memory = RuntimeMemory()
    return _runtime_memory


def init_runtime_session():
    memory = get_runtime_memory()
    memory.clear_session()
    return memory
