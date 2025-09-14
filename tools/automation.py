from __future__ import annotations
import platform
import subprocess
def paste(text:str)->dict:
    if platform.system().lower()=="darwin":
        try:
            p=subprocess.Popen("pbcopy", env={"LANG":"en_US.UTF-8"}, stdin=subprocess.PIPE)
            p.communicate(text.encode("utf-8"))
            return {"ok":True,"action":"paste-buffer-set","len":len(text)}
        except Exception as e: 
            return {"ok":False,"error":str(e)}
    return {"ok":True,"message":"no-op (not macOS)"}
TOOL_SPEC={"name":"automation","help":"Light automation","actions":{"paste":{"help":"clipboard paste","run":paste}}}
