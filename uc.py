from __future__ import annotations
import argparse
import json
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


def cmd_jarvis(a):
    import jarvis

    jarvis.loop(
        speech_enabled=not a.speech_off,
        watchdog_enabled=not a.no_watchdog,
        log_file=a.log_file,
    )


def main():
    ap = argparse.ArgumentParser(prog="uc", description="UltraJarvis v8")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("tools")
    p.set_defaults(func=cmd_tools)
    p = sub.add_parser("status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("seed")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--section", type=str, default=None)
    p.set_defaults(func=cmd_seed)
    p = sub.add_parser("run")
    p.add_argument("--batch", type=int, default=50)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("add")
    p.add_argument("item")
    p.add_argument("--section", default="Backlog")
    p.set_defaults(func=cmd_add)
    p = sub.add_parser("expand")
    p.add_argument("--goal", default="Expansion & hardening")
    p.add_argument("--phases", type=int, default=1)
    p.add_argument("--items-per-phase", type=int, default=12)
    p.set_defaults(func=cmd_expand)
    p = sub.add_parser("phase")
    p.set_defaults(func=cmd_phase)
    p = sub.add_parser("validate")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("health")
    p.add_argument(
        "action", nargs="?", choices=["status", "scan", "plan", "fix"], default="status"
    )
    p.set_defaults(func=cmd_health)

    p = sub.add_parser("track")
    sp = p.add_subparsers(dest="subcmd", required=True)
    lp = sp.add_parser("list")
    lp.set_defaults(func=cmd_track)
    ap2 = sp.add_parser("add")
    ap2.add_argument("name")
    ap2.set_defaults(func=cmd_track)

    p = sub.add_parser("jarvis")
    p.add_argument("--speech-off", action="store_true", help="Disable text-to-speech")
    p.add_argument(
        "--no-watchdog", action="store_true", help="Disable watchdog for debugging"
    )
    p.add_argument(
        "--log-file", default="logs/uj.log", help="Log file path (default: logs/uj.log)"
    )
    p.set_defaults(func=cmd_jarvis)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
