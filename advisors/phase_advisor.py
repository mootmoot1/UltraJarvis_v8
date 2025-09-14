from pathlib import Path
import json, datetime as dt

DATA = Path("data"); DATA.mkdir(exist_ok=True)
STORE = DATA / "phase.json"

def _load():
    if STORE.exists():
        try: return json.loads(STORE.read_text(encoding="utf-8"))
        except Exception: pass
    return {"goal": "", "history":[]}

def _save(d): STORE.write_text(json.dumps(d, indent=2), encoding="utf-8")

def set_goal(goal:str)->dict:
    d=_load(); d["goal"]=goal; d["updated"]=dt.datetime.utcnow().isoformat()+"Z"
    d["history"].append({"ts":dt.datetime.utcnow().isoformat()+"Z","event":"set_goal","goal":goal})
    _save(d); return {"ok":True,"goal":goal}

def status()->dict:
    d=_load(); return {"ok":True,"goal":d.get("goal",""),"last_updated":d.get("updated")}

def suggest_tasks(max_items:int=25)->dict:
    g=_load().get("goal","").strip() or "Empire Growth"
    buckets={"BUILD":["Design system architecture","Define KPIs","Create MVP feature list"],
             "MARKET":["Identify 5 customer segments","Draft landing page","Competitor scan (10)"],
             "OPS":["Weekly review ritual","Success dashboard","Risk register v1"],
             "GROWTH":["Channel tests plan","Outreach template v1","Partnerships research (10)"],
             "FINANCE":["Pricing hypotheses","Initial P&L skeleton","Payments/checkout plan"]}
    items=[]; 
    for k,vs in buckets.items():
        for v in vs:
            items.append(f"[{k}] {v} — {g}")
            if len(items)>=max_items: break
        if len(items)>=max_items: break
    return {"ok":True,"items":items,"goal":g}

def append_to_roadmap(items:list)->dict:
    p=Path("project/roadmap.md"); p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists(): p.write_text("# Roadmap\n\n", encoding="utf-8")
    md=p.read_text(encoding="utf-8")
    if "## Phase Advisor Suggestions" not in md: md += "\n## Phase Advisor Suggestions\n"
    md += "".join(f"- {it}\n" for it in items)
    p.write_text(md, encoding="utf-8")
    return {"ok":True,"wrote":len(items),"file":str(p)}
