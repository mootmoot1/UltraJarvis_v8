from __future__ import annotations
from pathlib import Path

def _safe(p:str)->Path:
    path=Path(p).expanduser().resolve()
    forbidden={Path("/"),Path("/System"),Path("/bin"),Path("/usr"),Path("/etc")}
    if any(str(path).startswith(str(f)) for f in forbidden) and not str(path).startswith("/tmp/"):
        raise ValueError("protected path")
    return path

def read(path:str, head:int=20, tail:int=20)->dict:
    try:
        p=_safe(path); 
        if not p.exists(): return {"ok":False,"error":f"not found: {p}"}
        lines=p.read_text(encoding="utf-8",errors="ignore").splitlines()
        prev=lines[:head]+(["…"] if len(lines)>head+tail else [])+(lines[-tail:] if len(lines)>head else [])
        return {"ok":True,"path":str(p),"lines":len(lines),"preview":prev}
    except Exception as e: return {"ok":False,"error":str(e)}

def write(path:str, content:str, confirm:bool=False, backup:bool=True)->dict:
    try:
        if not confirm: return {"ok":False,"error":"confirmation required","hint":"pass confirm=True"}
        p=_safe(path); p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists() and backup: p.with_suffix(p.suffix+".bak").write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
        p.write_text(content, encoding="utf-8"); return {"ok":True,"path":str(p),"bytes":len(content)}
    except Exception as e: return {"ok":False,"error":str(e)}

TOOL_SPEC={"name":"files","help":"Guarded file I/O","actions":{
 "default":{"help":"read","run":read},
 "read":{"help":"preview file","run":read},
 "write":{"help":"write (confirm)","run":write}
}}
