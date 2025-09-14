from __future__ import annotations
import time
import logging
from typing import Dict, List
from collections import defaultdict

logger = logging.getLogger(__name__)


class ToolWatchdog:
    def __init__(self, failure_threshold: int = 3, time_window: float = 60.0):
        self.failure_threshold = failure_threshold
        self.time_window = time_window
        self.failures: Dict[str, List[float]] = defaultdict(list)
        self.disabled_actions: Dict[str, float] = {}
        self.enabled = True

    def record_failure(self, tool: str, action: str) -> bool:
        if not self.enabled:
            return False

        key = f"{tool}.{action}"
        current_time = time.time()

        self.failures[key].append(current_time)

        recent_failures = [
            t for t in self.failures[key] if current_time - t <= self.time_window
        ]
        self.failures[key] = recent_failures

        if len(recent_failures) >= self.failure_threshold:
            self.disabled_actions[key] = current_time
            logger.warning(
                f"Disabling {key} after {len(recent_failures)} failures in {self.time_window}s"
            )
            return True

        return False

    def is_disabled(self, tool: str, action: str) -> bool:
        if not self.enabled:
            return False
        key = f"{tool}.{action}"
        return key in self.disabled_actions

    def get_disabled_message(self, tool: str, action: str) -> str:
        key = f"{tool}.{action}"
        if key in self.disabled_actions:
            return f"Action {key} is temporarily disabled due to repeated failures"
        return ""

    def get_status(self) -> Dict[str, any]:
        return {
            "enabled": self.enabled,
            "disabled_actions": list(self.disabled_actions.keys()),
            "failure_counts": {k: len(v) for k, v in self.failures.items()},
        }

    def reset_session(self):
        self.failures.clear()
        self.disabled_actions.clear()

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True


_global_watchdog: ToolWatchdog = None


def get_watchdog() -> ToolWatchdog:
    global _global_watchdog
    if _global_watchdog is None:
        _global_watchdog = ToolWatchdog()
    return _global_watchdog


def init_watchdog_session(enabled: bool = True) -> ToolWatchdog:
    watchdog = get_watchdog()
    watchdog.reset_session()
    if enabled:
        watchdog.enable()
    else:
        watchdog.disable()
    return watchdog
