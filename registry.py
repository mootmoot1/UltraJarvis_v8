from __future__ import annotations
import importlib
import pkgutil
import time
import signal
import logging
from typing import Dict, Any, Callable
from core.cache import get_tool_cache

logger = logging.getLogger(__name__)

_profiling_enabled = False
_profile_data: Dict[str, list] = {}


def discover_tools() -> Dict[str, dict]:
    reg: Dict[str, dict] = {}
    pkg = importlib.import_module("tools")
    for m in pkgutil.iter_modules(pkg.__path__):
        mod = importlib.import_module(f"tools.{m.name}")
        spec = getattr(mod, "TOOL_SPEC", None)
        if isinstance(spec, dict) and "name" in spec and "actions" in spec:
            reg[spec["name"]] = spec
    return reg


def run_tool(
    reg: Dict[str, dict], tool: str, action: str, args: Dict[str, Any]
) -> dict:
    try:
        from core.watchdog import get_watchdog

        watchdog = get_watchdog()

        if watchdog.is_disabled(tool, action):
            return {"ok": False, "error": watchdog.get_disabled_message(tool, action)}
    except ImportError:
        pass

    cache = get_tool_cache()
    cache_key_args = {
        k: v for k, v in (args or {}).items() if isinstance(v, (str, int, float, bool))
    }

    cached_result = cache.get(tool, action, cache_key_args)
    if cached_result is not None:
        if _profiling_enabled:
            _profile_data.setdefault(f"{tool}.{action}", []).append(0.001)
        return cached_result

    t = reg.get(tool)
    if not t:
        return {"ok": False, "error": f"unknown tool: {tool}"}
    a = action or "default"
    act = t["actions"].get(a) or t["actions"].get("default")
    if not act or not callable(act.get("run")):
        return {"ok": False, "error": f"tool/action not found: {tool}.{action}"}
    fn: Callable = act["run"]

    def timeout_handler(signum, frame):
        raise TimeoutError("Tool execution timeout")

    for attempt in range(3):
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(15)

            start_time = time.time()
            out = fn(**(args or {}))
            duration = time.time() - start_time
            duration_ms = int(duration * 1000)

            signal.alarm(0)

            if _profiling_enabled:
                _profile_data.setdefault(f"{tool}.{action}", []).append(duration)

            result = out if isinstance(out, dict) else {"ok": True, "result": out}
            success = result.get("ok", False)

            try:
                from runtime.metrics import get_metrics_collector

                metrics = get_metrics_collector()
                metrics.record_tool_execution(
                    tool, action, duration_ms, success, cached_result is not None
                )
            except ImportError:
                pass

            logger.info(
                f"Tool {tool}.{action} completed",
                extra={
                    "tool": f"{tool}.{action}",
                    "duration_ms": duration_ms,
                    "result": "ok" if success else "fail",
                    "cache_hit": cached_result is not None,
                },
            )

            if success:
                cache.set(tool, action, cache_key_args, result)

            return result

        except Exception as e:
            signal.alarm(0)
            duration = time.time() - start_time if "start_time" in locals() else 0

            duration_ms = int(duration * 1000) if "duration" in locals() else 0

            try:
                from runtime.metrics import get_metrics_collector

                metrics = get_metrics_collector()
                metrics.record_tool_execution(tool, action, duration_ms, False, False)
            except ImportError:
                pass

            logger.warning(
                f"Tool {tool}.{action} failed on attempt {attempt + 1}: {e}",
                extra={
                    "tool": f"{tool}.{action}",
                    "duration_ms": duration_ms,
                    "result": "fail",
                    "cache_hit": False,
                },
            )

            try:
                from core.watchdog import get_watchdog

                watchdog = get_watchdog()
                disabled = watchdog.record_failure(tool, action)
                if disabled:
                    try:
                        from tools.speech import speak

                        speak(
                            f"Temporarily disabling {tool}.{action} after repeated failures."
                        )
                    except ImportError:
                        pass
            except ImportError:
                pass

            if attempt == 2:
                return {
                    "ok": False,
                    "error": f"timeout or failure in {tool}.{action}",
                    "hint": "try again or use echo",
                }

            backoff_time = 0.5 * (3**attempt)
            time.sleep(backoff_time)

    return {
        "ok": False,
        "error": f"timeout or failure in {tool}.{action}",
        "hint": "try again or use echo",
    }


def describe_self(reg: Dict[str, dict]) -> dict:
    return {"ok": True, "tools": sorted(reg.keys())}


def enable_profiling():
    global _profiling_enabled
    _profiling_enabled = True
    _profile_data.clear()


def disable_profiling():
    global _profiling_enabled
    _profiling_enabled = False


def get_profile_data() -> Dict[str, Dict[str, Any]]:
    if not _profile_data:
        return {}

    stats = {}
    for tool_action, times in _profile_data.items():
        if times:
            stats[tool_action] = {
                "calls": len(times),
                "total_time": sum(times),
                "avg_time": sum(times) / len(times),
                "min_time": min(times),
                "max_time": max(times),
            }
    return stats


def print_profile_summary():
    if not _profiling_enabled:
        print("Profiling not enabled")
        return

    stats = get_profile_data()
    if not stats:
        print("No profiling data available")
        return

    print("\n=== Tool Performance Profile ===")
    for tool_action, data in sorted(
        stats.items(), key=lambda x: x[1]["total_time"], reverse=True
    ):
        print(f"{tool_action}:")
        print(f"  Calls: {data['calls']}")
        print(f"  Total: {data['total_time']:.3f}s")
        print(f"  Avg: {data['avg_time']:.3f}s")
        print(f"  Min: {data['min_time']:.3f}s")
        print(f"  Max: {data['max_time']:.3f}s")
    print("================================\n")
