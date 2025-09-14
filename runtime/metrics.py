from __future__ import annotations
import time
import statistics
from typing import Dict, Any, Optional, List


class MetricsCollector:
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            "runs": 0,
            "fails": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "tools": {},
            "latencies": [],
        }

    def record_tool_execution(
        self, tool: str, action: str, duration_ms: int, success: bool, cache_hit: bool
    ):
        self.metrics["runs"] += 1
        self.metrics["latencies"].append(duration_ms)

        if not success:
            self.metrics["fails"] += 1
        if cache_hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1

        tool_key = f"{tool}.{action}"
        if tool_key not in self.metrics["tools"]:
            self.metrics["tools"][tool_key] = {
                "calls": 0,
                "total_ms": 0,
                "failures": 0,
                "latencies": [],
            }

        self.metrics["tools"][tool_key]["calls"] += 1
        self.metrics["tools"][tool_key]["total_ms"] += duration_ms
        self.metrics["tools"][tool_key]["latencies"].append(duration_ms)
        if not success:
            self.metrics["tools"][tool_key]["failures"] += 1

    def _calculate_percentiles(self, latencies: List[int]) -> Dict[str, float]:
        """Calculate p50 and p95 percentiles from latency list"""
        if not latencies:
            return {"p50": 0.0, "p95": 0.0}

        sorted_latencies = sorted(latencies)
        return {
            "p50": statistics.median(sorted_latencies),
            "p95": (
                statistics.quantiles(sorted_latencies, n=20)[18]
                if len(sorted_latencies) >= 20
                else max(sorted_latencies)
            ),
        }

    def get_summary(self) -> Dict[str, Any]:
        avg_ms_by_tool = {}
        percentiles_by_tool = {}

        for tool, data in self.metrics["tools"].items():
            if data["calls"] > 0:
                avg_ms_by_tool[tool] = data["total_ms"] / data["calls"]
                percentiles_by_tool[tool] = self._calculate_percentiles(
                    data["latencies"]
                )

        overall_percentiles = self._calculate_percentiles(self.metrics["latencies"])
        error_rate = (
            (self.metrics["fails"] / self.metrics["runs"]) * 100
            if self.metrics["runs"] > 0
            else 0
        )

        return {
            "runs": self.metrics["runs"],
            "fails": self.metrics["fails"],
            "error_rate_percent": round(error_rate, 2),
            "cache_hits": self.metrics["cache_hits"],
            "cache_misses": self.metrics["cache_misses"],
            "avg_ms_by_tool": avg_ms_by_tool,
            "percentiles_by_tool": percentiles_by_tool,
            "overall_latency_p50": overall_percentiles["p50"],
            "overall_latency_p95": overall_percentiles["p95"],
            "uptime_seconds": int(time.time() - self.start_time),
        }


_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
