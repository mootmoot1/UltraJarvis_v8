from __future__ import annotations
import time
from typing import Dict, Any, Optional


class MetricsCollector:
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            "runs": 0,
            "fails": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "tools": {},
        }

    def record_tool_execution(
        self, tool: str, action: str, duration_ms: int, success: bool, cache_hit: bool
    ):
        self.metrics["runs"] += 1
        if not success:
            self.metrics["fails"] += 1
        if cache_hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1

        tool_key = f"{tool}.{action}"
        if tool_key not in self.metrics["tools"]:
            self.metrics["tools"][tool_key] = {"calls": 0, "total_ms": 0, "failures": 0}

        self.metrics["tools"][tool_key]["calls"] += 1
        self.metrics["tools"][tool_key]["total_ms"] += duration_ms
        if not success:
            self.metrics["tools"][tool_key]["failures"] += 1

    def get_summary(self) -> Dict[str, Any]:
        avg_ms_by_tool = {}
        for tool, data in self.metrics["tools"].items():
            if data["calls"] > 0:
                avg_ms_by_tool[tool] = data["total_ms"] / data["calls"]

        return {
            "runs": self.metrics["runs"],
            "fails": self.metrics["fails"],
            "cache_hits": self.metrics["cache_hits"],
            "cache_misses": self.metrics["cache_misses"],
            "avg_ms_by_tool": avg_ms_by_tool,
            "uptime_seconds": int(time.time() - self.start_time),
        }


_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
