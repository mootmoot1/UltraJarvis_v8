from __future__ import annotations
import uuid
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from core.persistence import get_persistent_memory
from memory.lru import get_note_cache


class EnhancedMemory:
    def __init__(self, db_path: str = None):
        if db_path:
            import os

            os.environ["MEMORY_DB_PATH"] = db_path
            from core.persistence import reset_persistent_memory

            reset_persistent_memory()
        self.persistence = get_persistent_memory()
        self.note_cache = get_note_cache()
        self.current_session_id = str(uuid.uuid4())
        self._start_session()

    def _start_session(self):
        import sqlite3

        with sqlite3.connect(self.persistence.db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (id, started_at) VALUES (?, ?)",
                (self.current_session_id, datetime.utcnow().isoformat() + "Z"),
            )

    def end_session(self):
        import sqlite3

        with sqlite3.connect(self.persistence.db_path) as conn:
            conn.execute(
                "UPDATE sessions SET ended_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat() + "Z", self.current_session_id),
            )

    def add_command(self, intent: str, text: str, success: bool, duration_ms: int):
        import sqlite3

        with sqlite3.connect(self.persistence.db_path) as conn:
            conn.execute(
                "INSERT INTO commands (session_id, intent, text, created_at, success, duration_ms) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    self.current_session_id,
                    intent,
                    text,
                    datetime.utcnow().isoformat() + "Z",
                    success,
                    duration_ms,
                ),
            )

    def get_recent_commands(self, limit: int = 10) -> List[Dict[str, Any]]:
        import sqlite3

        with sqlite3.connect(self.persistence.db_path) as conn:
            cursor = conn.execute(
                "SELECT intent, text, success, duration_ms FROM commands WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (self.current_session_id, limit),
            )
            return [
                {
                    "intent": row[0],
                    "text": row[1],
                    "success": bool(row[2]),
                    "duration_ms": row[3],
                }
                for row in cursor.fetchall()
            ]

    def add_note_with_cache(self, note: str, tag: str = "manual_note") -> bool:
        success = self.persistence.add_note(note, tag)
        if success:
            cache_key = f"{tag}:{note[:50]}"
            self.note_cache.put(
                cache_key,
                {"note": note, "tag": tag, "ts": datetime.utcnow().isoformat() + "Z"},
            )
        return success

    def get_cached_notes(self) -> List[Dict[str, Any]]:
        return self.note_cache.get_all()

    def forget_last_conversations(self, n: int = 1) -> bool:
        try:
            with sqlite3.connect(self.persistence.db_path) as conn:
                for _ in range(n):
                    conn.execute(
                        "DELETE FROM conversations WHERE session_id = ? AND id = (SELECT MAX(id) FROM conversations WHERE session_id = ?)",
                        (self.current_session_id, self.current_session_id),
                    )
            return True
        except Exception:
            return False


_enhanced_memory: Optional[EnhancedMemory] = None


def get_enhanced_memory() -> EnhancedMemory:
    global _enhanced_memory
    if _enhanced_memory is None:
        _enhanced_memory = EnhancedMemory()
    return _enhanced_memory
