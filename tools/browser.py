from __future__ import annotations
import webbrowser
import re

ALLOW = re.compile(r"^https?://", re.I)


def open_url(url: str) -> dict:
    if not url or not ALLOW.match(url.strip()):
        return {"ok": False, "error": "invalid url"}
    try:
        webbrowser.open(url)
        return {"ok": True, "opened": url}
    except Exception as e:
        return {"ok": False, "error": str(e)}


TOOL_SPEC = {
    "name": "browser",
    "help": "Open URLs",
    "actions": {"open_url": {"help": "open url", "run": open_url}},
}
