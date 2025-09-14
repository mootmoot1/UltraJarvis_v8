from __future__ import annotations
import json
import shlex
import subprocess
import platform
import logging
from datetime import datetime
from pathlib import Path
from registry import discover_tools, run_tool

MEM_PATH = Path("data/memory.json")
MEM_PATH.parent.mkdir(parents=True, exist_ok=True)
STATE = {"goal": None, "history": []}

def _load_mem():
    global STATE
    if MEM_PATH.exists():
        try: 
            STATE.update(json.loads(MEM_PATH.read_text(encoding="utf-8")))
        except Exception: 
            pass

def _save_mem():
    MEM_PATH.write_text(json.dumps(STATE, indent=2), encoding="utf-8")

def _speak(text:str):
    print(f"Jarvis: {text}")
    try:
        from tools.speech import speak
        speak(text)
    except ImportError:
        if platform.system().lower()=="darwin":
            try: 
                subprocess.run(["say", text], check=False)
            except Exception: 
                pass

def _append_history(user:str, bot:str):
    STATE["history"] = (STATE.get("history") or [])[-19:] + [{"ts":datetime.utcnow().isoformat()+"Z","user":user,"bot":bot}]
    _save_mem()
    try:
        from core.runtime import get_runtime_memory
        runtime_memory = get_runtime_memory()
        runtime_memory.add_turn(user, bot)
    except ImportError:
        pass

def _handle_set_goal(t:str):
    goal=t.split(" ",2)[2].strip() if " " in t else ""
    STATE["goal"]=goal
    _save_mem()
    return f"Goal set: {goal}"

def _handle_expand():
    from advisors import phase_advisor as phase
    sug = phase.suggest_tasks(max_items=25)
    if not sug.get("ok"): 
        return sug.get("error","no suggestions")
    app = phase.append_to_roadmap(sug["items"])
    return f"Added {app['wrote']} tasks to {app['file']}"

def _handle_health(t:str):
    from advisors import health_advisor as ha
    tl=t.lower()
    out = ha.scan() if "scan" in tl else ha.plan() if "plan" in tl or "upgrade" in tl else ha.fix() if "fix" in tl else ha.status()
    return f"Health: {json.dumps(out)}"

def _parse_kv(parts):
    kv={}
    for p in parts:
        if "=" in p:
            k,v=p.split("=",1)
            kv[k]=v
    return kv

def _handle_run_tool(t:str):
    # "run files read path=project/roadmap.md"
    parts=shlex.split(t)
    if len(parts)<3: 
        return "Usage: run <tool> <action> key=val ..."
    _, tool, action, *rest = parts
    kv=_parse_kv(rest)
    out=run_tool(discover_tools(), tool, action, kv)
    return json.dumps(out)

def _handle_memory(t:str):
    tl=t.lower()
    if tl.startswith("remember "):
        note=t.split(" ",1)[1]
        notes=STATE.setdefault("notes",[])
        notes.append({"ts":datetime.utcnow().isoformat()+"Z","note":note})
        _save_mem()
        return "Remembered."
    if tl=="show memory":
        return json.dumps({"goal":STATE.get("goal"),"notes":STATE.get("notes",[]),"turns":len(STATE.get("history",[]))})
    return "Try: remember <note> | show memory"

def _handle_note(t:str):
    note_text = t[5:].strip()
    notes = STATE.setdefault("notes", [])
    notes.append({
        "ts": datetime.utcnow().isoformat() + "Z",
        "note": note_text,
        "tag": "manual_note"
    })
    _save_mem()
    return f"Noted: {note_text}"

def loop(speech_enabled=True, watchdog_enabled=True, log_file="logs/uj.log"):
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                       handlers=[logging.FileHandler(log_path), logging.StreamHandler()])
    
    try:
        from tools.speech import init_speech_queue, shutdown_speech
        init_speech_queue(enabled=speech_enabled)
    except ImportError:
        pass
    
    try:
        from core.watchdog import init_watchdog_session
        init_watchdog_session(enabled=watchdog_enabled)
    except ImportError:
        pass
    
    try:
        from core.runtime import init_runtime_session
        init_runtime_session()
    except ImportError:
        pass
    
    _load_mem()
    _speak(f"Online. Goal: {STATE.get('goal') or '(none)'} | try: set goal <..>, expand phases, seed, run --batch 25, health scan, list tracks, add track content, show memory, note <text>.")
    
    try:
        while True:
            try: 
                s=input("You: ").strip()
            except EOFError: 
                break
            if not s: 
                continue
            if s.lower() in ("quit","exit"): 
                _speak("Goodbye.")
                break
            if s.lower().startswith("set goal "): 
                reply=_handle_set_goal(s)
            elif s.lower() in ("expand phases","expand phase","add phase tasks"): 
                reply=_handle_expand()
            elif s.lower().startswith("health"): 
                reply=_handle_health(s)
            elif s.lower().startswith("run "): 
                reply=_handle_run_tool(s)
            elif s.lower().startswith("note "): 
                reply=_handle_note(s)
            elif s.lower().startswith("remember") or s.lower()=="show memory": 
                reply=_handle_memory(s)
            elif s.lower().startswith("list tracks") or s.lower().startswith("add track "):
                from advisors import track_loader as tl
                reply = ", ".join(tl.list_tracks()["tracks"]) if s.lower().startswith("list tracks") else (lambda r: f"Added {r['added']} ({r['count']} items)." if r.get("ok") else f"Track add failed: {r.get('error')}")(tl.add_track(s.split(" ",2)[2]))
            elif s.lower()=="phase status":
                from tools import roadmap as rm
                reply=json.dumps(rm.phase_status())
            elif s.lower()=="seed":
                from registry import discover_tools, run_tool
                reply=json.dumps(run_tool(discover_tools(),"roadmap","seed",{}))
            elif s.lower().startswith("run --batch"):
                try: 
                    b=int(s.split()[-1])
                except ValueError: 
                    b=25
                reply=json.dumps(run_tool(discover_tools(),"roadmap","run",{"batch":b}))
            elif s.lower()=="status":
                reply=json.dumps(run_tool(discover_tools(),"roadmap","status",{}))
            else:
                reply=s
            _speak(reply)
            _append_history(s, reply)
    finally:
        try:
            from tools.speech import shutdown_speech
            shutdown_speech()
        except ImportError:
            pass
