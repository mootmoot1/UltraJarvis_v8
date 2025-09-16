from __future__ import annotations

SAFE_MODE = True


def send(to: str, subject: str, body: str, actually_send: bool = False) -> dict:
    if SAFE_MODE and not actually_send:
        prev = f"TO: {to}\nSUBJECT: {subject}\n\n{body[:300]}" + (
            "…" if len(body) > 300 else ""
        )
        return {"ok": True, "preview": prev, "sent": False, "note": "SAFE_MODE"}
    return {"ok": True, "sent": True}


def inbox(limit: int = 10) -> dict:
    return {
        "ok": True,
        "messages": [
            {"from": "demo@example.com", "subject": "Welcome", "snippet": "stub"}
        ],
    }


def search(q: str, limit: int = 10) -> dict:
    return {
        "ok": True,
        "matches": [
            {"from": "sales@example.com", "subject": f"About {q}", "snippet": "stub"}
        ],
    }


TOOL_SPEC = {
    "name": "email",
    "help": "Email stub",
    "actions": {
        "send": {"help": "send (safe)", "run": send},
        "inbox": {"help": "list inbox", "run": inbox},
        "search": {"help": "search inbox", "run": search},
    },
}
