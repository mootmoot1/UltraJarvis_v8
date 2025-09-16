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


def cmd_metrics(a):
    from runtime.metrics import get_metrics_collector

    metrics = get_metrics_collector()
    summary = metrics.get_summary()
    print(json.dumps(summary, indent=2))

    print("\nQuick Summary:")
    print(
        f"  Runs: {summary['runs']}, Fails: {summary['fails']} ({summary['error_rate_percent']}%)"
    )
    print(f"  Cache: {summary['cache_hits']} hits, {summary['cache_misses']} misses")
    print(
        f"  Latency: p50={summary['overall_latency_p50']:.1f}ms, p95={summary['overall_latency_p95']:.1f}ms"
    )


def cmd_memory(a):
    from memory.persistence import get_enhanced_memory

    memory = get_enhanced_memory()

    if a.subcmd == "view":
        limit = getattr(a, "limit", 50)
        tag = getattr(a, "tag", None)
        notes = memory.persistence.get_notes(limit=limit, tag=tag)
        cached_notes = memory.get_cached_notes()
        print(
            json.dumps(
                {
                    "notes": notes,
                    "cached_notes_count": len(cached_notes),
                    "recent_commands": memory.get_recent_commands(limit=10),
                },
                indent=2,
            )
        )
    elif a.subcmd == "forget-last":
        n = getattr(a, "n", 1)
        success = memory.forget_last_conversations(n)
        if success:
            print(f"Forgot last {n} conversations")
        else:
            print("Failed to forget conversations")
    elif a.subcmd == "clear-session":
        memory.end_session()
        print("Cleared current session")


def cmd_jarvis(a):
    import jarvis

    if a.forget_last:
        from core.persistence import get_persistent_memory

        memory = get_persistent_memory()
        memory.clear_last_conversation()
        print("Cleared last conversation from memory")
        return

    if a.clear_memory:
        from core.persistence import get_persistent_memory

        memory = get_persistent_memory()
        memory.clear_all_memory()
        print("Cleared all persistent memory")
        return

    jarvis.loop(
        speech_enabled=not a.speech_off,
        watchdog_enabled=not a.no_watchdog,
        log_file=a.log_file,
        profiling_enabled=a.profile,
    )


def cmd_devin(a):
    from tools.devin_agent import devin_agent
    result = devin_agent(a.task)
    print(json.dumps(result, indent=2))

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
    p.add_argument(
        "--profile",
        action="store_true",
        help="Enable per-tool execution time profiling",
    )
    p.add_argument(
        "--forget-last", action="store_true", help="Clear last conversation from memory"
    )
    p.add_argument(
        "--clear-memory", action="store_true", help="Clear all persistent memory"
    )
    p.set_defaults(func=cmd_jarvis)

    p = sub.add_parser("metrics")
    p.set_defaults(func=cmd_metrics)

    p = sub.add_parser("memory")
    sp = p.add_subparsers(dest="subcmd", required=True)

    view_p = sp.add_parser("view")
    view_p.add_argument("--limit", type=int, default=50)
    view_p.add_argument("--tag", type=str)
    view_p.set_defaults(func=cmd_memory)

    forget_p = sp.add_parser("forget-last")
    forget_p.add_argument("n", type=int, nargs="?", default=1)
    forget_p.set_defaults(func=cmd_memory)

    clear_p = sp.add_parser("clear-session")
    clear_p.set_defaults(func=cmd_memory)

    # Interactive Jarvis loop
    p = sub.add_parser("jarvis")
    p.set_defaults(func=cmd_jarvis)

    # Production developer agent (Devin)
    p = sub.add_parser("devin")
    p.add_argument("task", help="Natural language task description")
    p.set_defaults(func=cmd_devin)

    args = ap.parse_args()
    args.func(args)
    return


if __name__ == "__main__":
    main()
