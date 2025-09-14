def test_files_rw(tmp_path):
    from tools import files
    from unittest.mock import patch
    from pathlib import Path
    p=str(tmp_path/"x.txt")
    assert not files.write(p,"hi").get("ok")
    with patch.object(files, '_safe', return_value=Path(p)):
        assert files.write(p,"hi",confirm=True).get("ok")
        assert files.read(p).get("ok")

def test_websearch():
    from tools import websearch
    out=websearch.search("jarvis",k=2)
    assert out["ok"] and len(out["results"])==2
