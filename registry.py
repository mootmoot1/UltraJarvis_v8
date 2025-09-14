from __future__ import annotations
import importlib
import pkgutil
from typing import Dict, Any, Callable


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
    t = reg.get(tool)
    if not t:
        return {"ok": False, "error": f"unknown tool: {tool}"}
    a = action or "default"
    act = t["actions"].get(a) or t["actions"].get("default")
    if not act or not callable(act.get("run")):
        return {"ok": False, "error": f"tool/action not found: {tool}.{action}"}
    fn: Callable = act["run"]
    try:
        out = fn(**(args or {}))
        return out if isinstance(out, dict) else {"ok": True, "result": out}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def describe_self(reg: Dict[str, dict]) -> dict:
    return {"ok": True, "tools": sorted(reg.keys())}
