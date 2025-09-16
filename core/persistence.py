from __future__ import annotations
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PersistentMemory:
    def __init__(self, db_path: str = "data/memory.db"):
        import os

        actual_path = os.environ.get("MEMORY_DB_PATH", db_path)
        self.db_path = Path(actual_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    note TEXT NOT NULL,
                    tag TEXT DEFAULT 'manual_note'
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_input TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    session_id TEXT
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    ended_at TEXT
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """
            )

    def add_note(self, note: str, tag: str = "manual_note") -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO notes (timestamp, note, tag) VALUES (?, ?, ?)",
                    (datetime.utcnow().isoformat() + "Z", note, tag),
                )
            return True
        except Exception as e:
            logger.error(f"Failed to add note: {e}")
            return False

    def get_notes(
        self, limit: int = 50, tag: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                if tag:
                    cursor = conn.execute(
                        "SELECT timestamp, note, tag FROM notes WHERE tag = ? ORDER BY id DESC LIMIT ?",
                        (tag, limit),
                    )
                else:
                    cursor = conn.execute(
                        "SELECT timestamp, note, tag FROM notes ORDER BY id DESC LIMIT ?",
                        (limit,),
                    )
                return [
                    {"ts": row[0], "note": row[1], "tag": row[2]}
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Failed to get notes: {e}")
            return []

    def add_conversation(
        self, user_input: str, assistant_response: str, session_id: str = "default"
    ) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO conversations (timestamp, user_input, assistant_response, session_id) VALUES (?, ?, ?, ?)",
                    (
                        datetime.utcnow().isoformat() + "Z",
                        user_input,
                        assistant_response,
                        session_id,
                    ),
                )
            return True
        except Exception as e:
            logger.error(f"Failed to add conversation: {e}")
            return False

    def get_conversations(
        self, limit: int = 50, session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                if session_id:
                    cursor = conn.execute(
                        "SELECT timestamp, user_input, assistant_response FROM conversations WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                        (session_id, limit),
                    )
                else:
                    cursor = conn.execute(
                        "SELECT timestamp, user_input, assistant_response FROM conversations ORDER BY id DESC LIMIT ?",
                        (limit,),
                    )
                return [
                    {"ts": row[0], "user": row[1], "assistant": row[2]}
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Failed to get conversations: {e}")
            return []

    def search_notes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT timestamp, note, tag FROM notes WHERE note LIKE ? ORDER BY id DESC LIMIT ?",
                    (f"%{query}%", limit),
                )
                return [
                    {"ts": row[0], "note": row[1], "tag": row[2]}
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Failed to search notes: {e}")
            return []

    def clear_last_conversation(self, session_id: str = "default") -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM conversations WHERE session_id = ? AND id = (SELECT MAX(id) FROM conversations WHERE session_id = ?)",
                    (session_id, session_id),
                )
            return True
        except Exception as e:
            logger.error(f"Failed to clear last conversation: {e}")
            return False

    def clear_all_memory(self) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM notes")
                conn.execute("DELETE FROM conversations")
            return True
        except Exception as e:
            logger.error(f"Failed to clear all memory: {e}")
            return False


_persistent_memory: Optional[PersistentMemory] = None


def get_persistent_memory() -> PersistentMemory:
    global _persistent_memory
    if _persistent_memory is None:
        _persistent_memory = PersistentMemory()
    return _persistent_memory


def reset_persistent_memory():
    global _persistent_memory
    _persistent_memory = None
