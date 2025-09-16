from __future__ import annotations
import argparse
import json
import logging
from pathlib import Path

from registry import discover_tools, run_tool


def cmd_tools(a):
    print(json.dumps({"ok": True, "tools": sorted(discover_tools().keys())}))


def cmd_status(a):
    print(json.dumps(run_tool(discover_tools(), "roadmap", "status", {})))


def cmd_seed(a):
    kw = {}
    if a.limit is not None:
        kw["limit"] = a.limit
    if a.section:
        kw["section"] = a.section
    print(json.dumps(run_tool(discover_tools(), "roadmap", "seed", kw)))


def cmd_run(a):
    print(json.dumps(run_tool(discover_tools(), "roadmap", "run", {"batch": a.batch})))


def cmd_add(a):
    print(
        json.dumps(
            run_tool(
                discover_tools(),
                "roadmap",
                "add",
                {"item": a.item, "section": a.section},
            )
        )
    )


def cmd_expand(a):
    print(
        json.dumps(
            run_tool(
                discover_tools(),
                "roadmap",
                "expand",
                {
                    "goal": a.goal,
                    "phases": a.phases,
                    "items_per_phase": a.items_per_phase,
                },
            )
        )
    )


def cmd_phase(a):
    print(json.dumps(run_tool(discover_tools(), "roadmap", "phase", {})))


def cmd_validate(a):
    print(json.dumps(run_tool(discover_tools(), "roadmap", "validate", {})))


def cmd_health(a):
    from advisors import health_advisor as ha

    act = a.action
    out = (
        ha.status()
        if act == "status"
        else ha.scan() if act == "scan" else ha.plan() if act == "plan" else ha.fix()
    )
    print(json.dumps(out))


def cmd_track(a):
    from advisors import track_loader as tl

    out = tl.list_tracks() if a.subcmd == "list" else tl.add_track(a.name)
    print(json.dumps(out))


# ---- commands (handlers) ----

def cmd_jarvis(a):
    try:
        from jarvis import loop
        loop(
            speech_enabled=not getattr(a, "speech_off", False),
            watchdog_enabled=not getattr(a, "no_watchdog", False),
            log_file=getattr(a, "log_file", "logs/uj.log"),
            profiling_enabled=getattr(a, "profile", False),
        )
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))

def cmd_devin(a):
    # Production developer agent
    try:
        from tools.devin_agent import run_task
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"devin agent unavailable: {e}"}))
        return
    print(json.dumps(run_task(a.task)))


# ---- argparse wiring ----

def main():
    ap = argparse.ArgumentParser(prog="uj")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # tools
    p = sub.add_parser("tools")
    p.set_defaults(func=lambda a: print(json.dumps({"ok": True, "tools": sorted(discover_tools().keys())})))

    # status
    p = sub.add_parser("status")
    p.set_defaults(func=lambda a: print(json.dumps(run_tool(discover_tools(), "roadmap", "status", {}))))

    # seed
    p = sub.add_parser("seed")
    p.add_argument("--limit", type=int)
    p.add_argument("--section", type=str)
    def _seed(a):
        kw = {}
        if a.limit is not None: kw["limit"] = a.limit
        if a.section: kw["section"] = a.section
        print(json.dumps(run_tool(discover_tools(), "roadmap", "seed", kw)))
    p.set_defaults(func=_seed)

    # run
    p = sub.add_parser("run")
    p.add_argument("--batch", type=int, default=50)
    p.set_defaults(func=lambda a: print(json.dumps(run_tool(discover_tools(), "roadmap", "run", {"batch": a.batch}))))

    # health
    p = sub.add_parser("health")
    p.add_argument("action", choices=["status", "scan", "plan", "fix"], nargs="?", default="status")
    def _health(a):
        print(json.dumps(run_tool(discover_tools(), "health", a.action, {})))
    p.set_defaults(func=_health)

    # jarvis (interactive loop)
    p = sub.add_parser("jarvis")
    p.add_argument("--speech-off", action="store_true", help="disable text-to-speech")
    p.add_argument("--no-watchdog", action="store_true", help="disable watchdog")
    p.add_argument("--log-file", default="logs/uj.log", help="log file")
    p.add_argument("--profile", action="store_true", help="enable simple timing/profiling")
    p.add_argument("--forget-last", type=int, default=0, help="clear last N conv turns (legacy; optional)")
    p.add_argument("--clear-memory", action="store_true", help="clear persistent memory (legacy; optional)")
    p.set_defaults(func=cmd_jarvis)

    # devin (production developer agent)
    p = sub.add_parser("devin")
    p.add_argument("task", help="Natural language task description")
    p.set_defaults(func=cmd_devin)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()