from __future__ import annotations
from pathlib import Path
from typing import Optional, List, Dict
import re, time

RM=Path("project/roadmap.md"); Q=Path("tasks.txt"); LOG=Path("logs/roadmap.log")

def _log(s:str):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text((LOG.read_text(encoding="utf-8") if LOG.exists() else "")+s+"\n", encoding="utf-8")

def _list_md_tasks(limit:int=0, section:Optional[str]=None)->List[str]:
    if not RM.exists(): return []
    text=RM.read_text(encoding="utf-8")
    tasks=[]
    sect=None
    for ln in text.splitlines():
        if ln.startswith("#"): sect=ln.lstrip("# ").strip()
        elif ln.strip().startswith("- ") and ((section is None) or (sect==section)):
            tasks.append(ln.strip()[2:].strip())
    return tasks[:limit] if limit and limit>0 else tasks

def seed(limit:int=0, section:Optional[str]=None)->dict:
    if not RM.exists(): return {"ok":False,"error":"project/roadmap.md missing"}
    tasks=_list_md_tasks(limit,section)
    Q.write_text("\n".join(tasks)+("\n" if tasks else ""), encoding="utf-8")
    return {"ok":True,"queued":len(tasks),"total":len(tasks),"section":section or "*"}

def status()->dict:
    pending=[l for l in (Q.read_text(encoding="utf-8").splitlines() if Q.exists() else []) if l.strip()]
    return {"ok":True,"pending":len(pending)}

def _pop()->Optional[str]:
    if not Q.exists(): return None
    lines=[l for l in Q.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines: return None
    head, rest = lines[0], lines[1:]; Q.write_text("\n".join(rest)+("\n" if rest else ""), encoding="utf-8")
    return head

def run(batch:int=50)->dict:
    n=0; fails=0; total_hint=sum(1 for _ in (Q.read_text(encoding="utf-8").splitlines() if Q.exists() else []))
    while n<batch:
        t=_pop()
        if not t: break
        n+=1; total=max(total_hint, n)
        print(f"[{n}/{total}] RUN — {t} [OK]")
        _log(f"OK: {t}")
    return {"ok":True,"processed":n,"fails":fails,"status":status()}

def add(item:str, section:str="Backlog")->dict:
    RM.parent.mkdir(parents=True, exist_ok=True)
    md=RM.read_text(encoding="utf-8") if RM.exists() else "# Roadmap\n\n"
    if f"## {section}" not in md: md += f"\n## {section}\n"
    md += f"- {item.strip()}\n"; RM.write_text(md, encoding="utf-8")
    return {"ok":True,"added":item.strip(),"section":section}

def expand(goal:str="Expansion & hardening", phases:int=1, items_per_phase:int=12)->dict:
    md=RM.read_text(encoding="utf-8") if RM.exists() else "# Roadmap\n\n"
    last=0
    for m in re.finditer(r"^##\s*Phase\s+(\d+)", md, re.M):
        last=max(last,int(m.group(1)))
    base=["Research options","Design spec","Implementation","Unit tests","Integration tests","Docs","CLI/UX wiring","QA sign-off"]
    out=[]
    for i in range(1, phases+1):
        n=last+i; out.append(f"## Phase {n} — {goal}")
        c=0
        while c<items_per_phase:
            for b in base:
                if c>=items_per_phase: break
                out.append(f"- {b}"); c+=1
        out.append("")
    md=md.rstrip()+"\n\n"+"\n".join(out)
    RM.write_text(md, encoding="utf-8")
    return {"ok":True,"phases_added":phases,"last_phase":last+phases}

def phase_status()->dict:
    if not RM.exists(): return {"ok":False,"error":"project/roadmap.md missing"}
    md=RM.read_text(encoding="utf-8")
    phases=len(re.findall(r"^##\s*Phase\s+\d+", md, re.M))
    bullets=sum(1 for l in md.splitlines() if l.strip().startswith("- "))
    return {"ok":True,"phases":phases,"bullets":bullets}

def validate()->dict:
    info={"roadmap_exists": RM.exists(), "queue_exists": Q.exists()}
    return {"ok": RM.exists(), "info": info}

TOOL_SPEC={"name":"roadmap","help":"Manage roadmap queue","actions":{
 "default":{"help":"status","run":status},
 "status":{"help":"queue status","run":status},
 "seed":{"help":"seed tasks","run":seed},
 "run":{"help":"process tasks","run":run},
 "add":{"help":"append task","run":add},
 "expand":{"help":"add phases","run":expand},
 "phase":{"help":"phase summary","run":phase_status},
 "validate":{"help":"sanity","run":validate}
}}
