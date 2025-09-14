from __future__ import annotations
import importlib
import pkgutil
import time
import signal
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)

def discover_tools() -> Dict[str, dict]:
    reg: Dict[str, dict] = {}
    pkg = importlib.import_module("tools")
    for m in pkgutil.iter_modules(pkg.__path__):
        mod = importlib.import_module(f"tools.{m.name}")
        spec = getattr(mod, "TOOL_SPEC", None)
        if isinstance(spec, dict) and "name" in spec and "actions" in spec:
            reg[spec["name"]] = spec
    return reg

def run_tool(reg: Dict[str, dict], tool: str, action: str, args: Dict[str, Any]) -> dict:
    try:
        from core.watchdog import get_watchdog
        watchdog = get_watchdog()
        
        if watchdog.is_disabled(tool, action):
            return {"ok": False, "error": watchdog.get_disabled_message(tool, action)}
    except ImportError:
        pass
    
    t = reg.get(tool)
    if not t: 
        return {"ok": False, "error": f"unknown tool: {tool}"}
    a = (action or "default")
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
            
            signal.alarm(0)
            
            logger.info(f"Tool {tool}.{action} completed in {duration:.2f}s (attempt {attempt + 1})")
            return out if isinstance(out, dict) else {"ok": True, "result": out}
            
        except Exception as e:
            signal.alarm(0)
            duration = time.time() - start_time if 'start_time' in locals() else 0
            
            logger.warning(f"Tool {tool}.{action} failed on attempt {attempt + 1}: {e} (duration: {duration:.2f}s)")
            
            try:
                from core.watchdog import get_watchdog
                watchdog = get_watchdog()
                disabled = watchdog.record_failure(tool, action)
                if disabled:
                    try:
                        from tools.speech import speak
                        speak(f"Temporarily disabling {tool}.{action} after repeated failures.")
                    except ImportError:
                        pass
            except ImportError:
                pass
            
            if attempt == 2:
                return {"ok": False, "error": f"timeout or failure in {tool}.{action}", "hint": "try again or use echo"}
            
            backoff_time = 0.5 * (3 ** attempt)
            time.sleep(backoff_time)
    
    return {"ok": False, "error": f"timeout or failure in {tool}.{action}", "hint": "try again or use echo"}

def describe_self(reg: Dict[str, dict]) -> dict:
    return {"ok": True, "tools": sorted(reg.keys())}
