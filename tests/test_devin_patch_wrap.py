import pytest
import tempfile
from pathlib import Path
from tools.devin_agent import _wrap_raw_content_to_diff, _is_protected_path


def test_raw_content_wrapper_new_file():
    """Test that raw content gets wrapped into valid unified diff for new files"""
    raw_content = "def hello():\n    print('world')\n"
    diff = _wrap_raw_content_to_diff("test.py", raw_content, is_new=True)

    assert "diff --git a/test.py b/test.py" in diff
    assert "new file mode 100644" in diff
    assert "+def hello():" in diff
    assert "+    print('world')" in diff


def test_raw_content_wrapper_existing_file():
    """Test that raw content gets wrapped into valid unified diff for existing files"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("old content\n")
        temp_path = f.name

    try:
        raw_content = "new content\n"
        diff = _wrap_raw_content_to_diff(temp_path, raw_content, is_new=False)

        assert "diff --git" in diff
        assert "-old content" in diff
        assert "+new content" in diff
    finally:
        Path(temp_path).unlink()


def test_protected_paths():
    """Test that protected paths are correctly identified"""
    assert _is_protected_path(".github/workflows/ci.yml") == True
    assert _is_protected_path("pyproject.toml") == True
    assert _is_protected_path("setup.py") == True
    assert _is_protected_path(".git/config") == True
    assert _is_protected_path(".venv/lib/python") == True
    assert _is_protected_path("ultra_jarvis.egg-info/PKG-INFO") == True

    assert _is_protected_path("tools/test.py") == False
    assert _is_protected_path("tests/test_example.py") == False
    assert _is_protected_path("README.md") == False


@pytest.mark.slow
def test_sandbox_worktree_flow():
    """Test sandbox worktree mode (can be skipped by default)"""
    pytest.skip("Sandbox worktree test requires git repository setup")
