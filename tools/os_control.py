from __future__ import annotations
import platform
import subprocess


def _is_mac():
    return platform.system().lower() == "darwin"


def volume(level: int) -> dict:
    if level < 0 or level > 100:
        return {"ok": False, "error": "level 0..100"}
    if not _is_mac():
        return {"ok": True, "message": f"no-op (not macOS) {level}"}
    try:
        subprocess.run(
            ["osascript", "-e", f"set volume output volume {level}"], check=True
        )
        return {"ok": True, "level": level}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def app_open(name: str) -> dict:
    if not name:
        return {"ok": False, "error": "empty app name"}
    if not _is_mac():
        return {"ok": True, "message": f"no-op (not macOS) {name}"}
    try:
        subprocess.run(["open", "-a", name], check=True)
        return {"ok": True, "opened": name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


TOOL_SPEC = {
    "name": "os_control",
    "help": "OS controls",
    "actions": {
        "volume": {"help": "0..100", "run": volume},
        "app_open": {"help": "open app", "run": app_open},
    },
}
