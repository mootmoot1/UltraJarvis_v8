from __future__ import annotations
import hashlib
import json
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ToolCache:
    def __init__(self, max_size: int = 128, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _generate_key(self, tool: str, action: str, args: Dict[str, Any]) -> str:
        content = f"{tool}.{action}:{json.dumps(args, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(
        self, tool: str, action: str, args: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        key = self._generate_key(tool, action, args)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl_seconds:
                logger.debug(f"Cache hit for {tool}.{action}")
                return entry["result"]
            else:
                del self.cache[key]
        return None

    def set(self, tool: str, action: str, args: Dict[str, Any], result: Dict[str, Any]):
        if len(self.cache) >= self.max_size:
            oldest_key = min(
                self.cache.keys(), key=lambda k: self.cache[k]["timestamp"]
            )
            del self.cache[oldest_key]

        key = self._generate_key(tool, action, args)
        self.cache[key] = {"result": result, "timestamp": time.time()}
        logger.debug(f"Cached result for {tool}.{action}")

    def clear(self):
        self.cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
        }


_tool_cache: Optional[ToolCache] = None


def get_tool_cache() -> ToolCache:
    global _tool_cache
    if _tool_cache is None:
        _tool_cache = ToolCache()
    return _tool_cache
