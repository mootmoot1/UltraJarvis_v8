import json
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_files_rw(tmp_path):
    from tools import files
    from unittest.mock import patch

    with patch.object(files, "_safe") as mock_safe:
        test_file = tmp_path / "x.txt"
        mock_safe.return_value = test_file

        p = str(test_file)

        result = files.write(p, "hi")
        assert not result.get("ok")
        assert "confirmation required" in result.get("error", "")

        result = files.write(p, "hi", confirm=True)
        assert result.get("ok")

        result = files.read(p)
        assert result.get("ok")


def test_websearch():
    from tools import websearch

    out = websearch.search("jarvis", k=2)
    assert out["ok"] and len(out["results"]) == 2


def test_roadmap_seed_and_status(tmp_path):
    """Test roadmap.seed() and status() with temp project/roadmap.md"""
    from tools import roadmap

    original_rm = roadmap.RM
    original_q = roadmap.Q
    temp_rm = tmp_path / "roadmap.md"
    temp_q = tmp_path / "tasks.txt"

    try:
        roadmap.RM = temp_rm
        roadmap.Q = temp_q

        temp_rm.write_text(
            "# Test Roadmap\n\n## Phase 1\n- Task 1\n- Task 2\n\n## Backlog\n- Task 3\n"
        )

        result = roadmap.seed(limit=2)
        assert result["ok"] is True
        assert result["queued"] == 2
        assert result["total"] == 2

        status_result = roadmap.status()
        assert status_result["ok"] is True
        assert status_result["pending"] == 2

        section_result = roadmap.seed(section="Backlog")
        assert section_result["ok"] is True
        assert section_result["queued"] == 1
        assert section_result["section"] == "Backlog"

    finally:
        roadmap.RM = original_rm
        roadmap.Q = original_q


def test_jarvis_loop_parsing():
    """Test uj-jarvis loop parsing simple commands without side-effects"""
    import jarvis

    with patch.object(jarvis, "_speak") as mock_speak:
        with patch("builtins.input", side_effect=["quit"]):
            with (
                patch.object(jarvis, "_load_mem"),
                patch.object(jarvis, "_save_mem"),
                patch.object(jarvis, "_append_history"),
            ):

                jarvis.loop()

                assert mock_speak.call_count >= 2
                mock_speak.assert_any_call("Goodbye.")


def test_health_advisor_scan():
    """Test advisors.health_advisor.scan() returns ok with expected keys"""
    from advisors import health_advisor

    with (
        patch("advisors.health_advisor.STATE") as mock_state,
        patch("advisors.health_advisor.LOG") as mock_log,
        patch.object(health_advisor, "_log"),
    ):

        mock_state.write_text = MagicMock()
        mock_log.write_text = MagicMock()

        result = health_advisor.scan()

        assert isinstance(result, dict)
        assert "ok" in result
        assert "checks" in result
        assert isinstance(result["checks"], list)

        for check in result["checks"]:
            assert "name" in check
            assert "ok" in check
            assert "info" in check
            assert isinstance(check["ok"], bool)


def test_health_advisor_status():
    """Test health_advisor.status() returns expected structure"""
    from advisors import health_advisor

    mock_state = {"ts": 1234567890, "last_ok": True, "checks": []}
    mock_logs = ["log line 1", "log line 2"]

    with (
        patch("advisors.health_advisor.STATE") as mock_state_path,
        patch("advisors.health_advisor.LOG") as mock_log_path,
    ):

        mock_state_path.exists.return_value = True
        mock_state_path.read_text.return_value = json.dumps(mock_state)
        mock_log_path.exists.return_value = True
        mock_log_path.read_text.return_value = "\n".join(mock_logs)

        result = health_advisor.status()

        assert result["ok"] is True
        assert "state" in result
        assert "log_tail" in result
        assert result["state"] == mock_state
        assert result["log_tail"] == mock_logs


def test_registry_discover_tools():
    """Test registry.discover_tools() returns expected tools"""
    from registry import discover_tools

    tools = discover_tools()

    assert isinstance(tools, dict)

    assert "roadmap" in tools
    assert "name" in tools["roadmap"]
    assert "actions" in tools["roadmap"]
    assert tools["roadmap"]["name"] == "roadmap"


def test_registry_run_tool():
    """Test registry.run_tool() executes tool actions correctly"""
    from registry import discover_tools, run_tool

    tools = discover_tools()

    result = run_tool(tools, "roadmap", "validate", {})
    assert isinstance(result, dict)
    assert "ok" in result

    result = run_tool(tools, "nonexistent", "action", {})
    assert result["ok"] is False
    assert "unknown tool" in result["error"]

    result = run_tool(tools, "websearch", "nonexistent_action", {})
    assert result["ok"] is False
    assert "tool/action not found" in result["error"]


def test_roadmap_additional_functions():
    """Test additional roadmap functions for better coverage"""
    from tools import roadmap

    original_rm = roadmap.RM
    original_q = roadmap.Q
    temp_rm = Path("/tmp/test_roadmap.md")
    temp_q = Path("/tmp/test_tasks.txt")

    try:
        roadmap.RM = temp_rm
        roadmap.Q = temp_q

        temp_rm.write_text("# Test\n\n## Phase 1\n- Task 1\n")
        temp_q.write_text("task1\ntask2\n")

        result = roadmap.validate()
        assert result["ok"] is True

        result = roadmap.run(batch=1)
        assert result["ok"] is True
        assert result["processed"] == 1

        result = roadmap.add("New task", section="Phase 1")
        assert result["ok"] is True

    finally:
        roadmap.RM = original_rm
        roadmap.Q = original_q
        if temp_rm.exists():
            temp_rm.unlink()
        if temp_q.exists():
            temp_q.unlink()


def test_files_additional_functions():
    """Test additional files functions for better coverage"""
    from tools import files
    from unittest.mock import patch

    with patch.object(files, "_safe") as mock_safe:
        test_file = Path("/tmp/test_read.txt")
        test_file.write_text("test content")
        mock_safe.return_value = test_file

        result = files.read(str(test_file))
        assert result["ok"] is True
        assert "preview" in result
        assert result["lines"] == 1

        test_file.unlink()


def test_browser_tool():
    """Test browser tool for coverage"""
    from tools import browser

    result = browser.open_url("https://example.com")
    assert isinstance(result, dict)
    assert "ok" in result


def test_email_tool():
    """Test email tool for coverage"""
    from tools import email

    result = email.send("test@example.com", "Test", "Body")
    assert isinstance(result, dict)
    assert "ok" in result


def test_automation_tool():
    """Test automation tool for coverage"""
    from tools import automation

    result = automation.paste("test text")
    assert isinstance(result, dict)
    assert "ok" in result


def test_os_control_tool():
    """Test os_control tool for coverage"""
    from tools import os_control

    result = os_control.volume(50)
    assert isinstance(result, dict)
    assert "ok" in result

    result = os_control.app_open("TextEdit")
    assert isinstance(result, dict)
    assert "ok" in result


def test_health_advisor_additional():
    """Test additional health_advisor functions for coverage"""
    from advisors import health_advisor
    from unittest.mock import patch, MagicMock

    with (
        patch("advisors.health_advisor.STATE") as mock_state,
        patch("advisors.health_advisor.LOG") as mock_log,
    ):

        mock_state.write_text = MagicMock()
        mock_log.write_text = MagicMock()

        result = health_advisor.plan()
        assert isinstance(result, dict)
        assert "ok" in result

        result = health_advisor.fix()
        assert isinstance(result, dict)
        assert "ok" in result


def test_phase_advisor():
    """Test phase_advisor for coverage"""
    from advisors import phase_advisor

    result = phase_advisor.suggest_tasks(max_items=5)
    assert isinstance(result, dict)
    assert "ok" in result
    assert "items" in result

    result = phase_advisor.status()
    assert isinstance(result, dict)
    assert "ok" in result

    result = phase_advisor.set_goal("Test goal")
    assert isinstance(result, dict)
    assert "ok" in result


def test_track_loader():
    """Test track_loader for coverage"""
    from advisors import track_loader

    result = track_loader.list_tracks()
    assert isinstance(result, dict)
    assert "ok" in result
    assert "tracks" in result

    result = track_loader.add_track("test_track")
    assert isinstance(result, dict)
    assert "ok" in result
