from pathlib import Path
import json
import time
import importlib

STATE = Path("data/health_state.json")
LOG = Path("logs/health.log")
STATE.parent.mkdir(exist_ok=True, parents=True)
LOG.parent.mkdir(exist_ok=True, parents=True)


def _log(s):
    LOG.write_text(
        (LOG.read_text() if LOG.exists() else "") + s + "\n", encoding="utf-8"
    )


def scan() -> dict:
    out = {"ok": True, "checks": []}

    def add(name, ok, info=""):
        out["checks"].append({"name": name, "ok": bool(ok), "info": info})
        if not ok:
            out["ok"] = False

    for f in ["uc.py", "jarvis.py", "registry.py", "project/roadmap.md"]:
        add(f"file:{f}", Path(f).exists(), "missing" if not Path(f).exists() else "")
    try:
        import registry

        reg = importlib.reload(registry).discover_tools()
        add("registry.discover_tools", True, f"tools={sorted(reg.keys())}")
    except Exception as e:
        add("registry.discover_tools", False, str(e))
    STATE.write_text(
        json.dumps(
            {"ts": time.time(), "last_ok": out["ok"], "checks": out["checks"]}, indent=2
        ),
        encoding="utf-8",
    )
    _log(f"scan ok={out['ok']}")
    return out


def plan() -> dict:
    tips = []
    try:
        import registry
        import importlib

        reg = importlib.reload(registry).discover_tools()
        for t in [
            "files",
            "websearch",
            "browser",
            "os_control",
            "email",
            "automation",
            "roadmap",
        ]:
            if t not in reg:
                tips.append(f"Add tool '{t}'")
    except Exception:
        tips.append("Registry failing — fix imports")
    if not Path("advisors/phase_advisor.py").exists():
        tips.append("Install Phase Advisor")
    return {"ok": True, "tips": tips}


def fix() -> dict:
    created = []
    for d in ["logs", "project", "advisors", "data", "tools", "backup"]:
        dp = Path(d)
        if not dp.exists():
            dp.mkdir(parents=True, exist_ok=True)
            created.append(d)
    _log(f"fix created={created}")
    return {"ok": True, "created": created}


def status() -> dict:
    s = STATE.read_text(encoding="utf-8") if STATE.exists() else "{}"
    return {
        "ok": True,
        "state": json.loads(s or "{}"),
        "log_tail": (
            LOG.read_text(encoding="utf-8").splitlines()[-20:] if LOG.exists() else []
        ),
    }
