from __future__ import annotations
import time
from typing import Dict, Any, Optional, List
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int = 200, ttl_seconds: int = 86400):
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        return time.time() - entry["timestamp"] > self.ttl_seconds

    def _evict_expired(self):
        expired_keys = []
        for key, entry in self.cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)
        for key in expired_keys:
            del self.cache[key]

    def get(self, key: str) -> Optional[Any]:
        self._evict_expired()
        if key in self.cache:
            entry = self.cache[key]
            if not self._is_expired(entry):
                self.cache.move_to_end(key)
                return entry["value"]
            else:
                del self.cache[key]
        return None

    def put(self, key: str, value: Any):
        self._evict_expired()

        if key in self.cache:
            self.cache[key] = {"value": value, "timestamp": time.time()}
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
            self.cache[key] = {"value": value, "timestamp": time.time()}

    def get_all(self) -> List[Any]:
        self._evict_expired()
        return [entry["value"] for entry in self.cache.values()]

    def clear(self):
        self.cache.clear()

    def size(self) -> int:
        self._evict_expired()
        return len(self.cache)


_note_cache: Optional[LRUCache] = None


def get_note_cache() -> LRUCache:
    global _note_cache
    if _note_cache is None:
        _note_cache = LRUCache(capacity=200, ttl_seconds=86400)
    return _note_cache


def reset_note_cache():
    global _note_cache
    _note_cache = None
