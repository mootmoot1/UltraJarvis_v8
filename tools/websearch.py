from __future__ import annotations
def search(query:str, k:int=3)->dict:
    q=(query or "").strip()
    if not q: return {"ok":False,"error":"empty query"}
    return {"ok":True,"results":[{"title":f"Result {i+1} for {q}","url":f"https://example.com/{i+1}","snippet":f"About {q}"} for i in range(max(1,min(k,5)))]}
TOOL_SPEC={"name":"websearch","help":"Safe stub","actions":{"search":{"help":"search","run":search}}}
