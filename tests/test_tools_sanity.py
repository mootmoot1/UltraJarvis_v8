def test_files_rw(tmp_path):
    from tools import files
    p=str(tmp_path/"x.txt")
    assert not files.write(p,"hi").get("ok")
    assert files.write(p,"hi",confirm=True).get("ok")
    assert files.read(p).get("ok")

def test_websearch():
    from tools import websearch
    out=websearch.search("jarvis",k=2)
    assert out["ok"] and len(out["results"])==2
