import time
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path


def test_speech_queue_drop_oldest():
    """Test speech queue drops oldest when full"""
    from tools.speech import SpeechQueue

    with patch("tools.speech.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.wait.return_value = None
        mock_popen.return_value = mock_proc

        queue = SpeechQueue(maxsize=2, enabled=True)
        queue.start()

        queue.enqueue("message1")
        queue.enqueue("message2")
        queue.enqueue("message3")

        time.sleep(0.2)
        queue.stop()

        assert mock_popen.call_count <= 2


def test_speech_queue_timeout():
    """Test speech queue handles TTS timeouts"""
    from tools.speech import SpeechQueue
    import subprocess

    with (
        patch("tools.speech.platform.system", return_value="Darwin"),
        patch("tools.speech.subprocess.Popen") as mock_popen,
    ):
        mock_proc = MagicMock()
        mock_proc.wait.side_effect = subprocess.TimeoutExpired("say", 0.1)
        mock_popen.return_value = mock_proc

        queue = SpeechQueue(maxsize=5, timeout=0.1, enabled=True)
        queue.start()

        queue.enqueue("test message")
        time.sleep(0.3)
        queue.stop()

        assert mock_popen.called


def test_timeout_retry_wrapper():
    """Test timeout/retry wrapper with monkeypatched tool"""
    from registry import run_tool
    from core.watchdog import init_watchdog_session

    init_watchdog_session()

    call_count = 0

    def failing_tool():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Simulated failure")
        return {"ok": True, "result": "success"}

    reg = {"test": {"actions": {"fail": {"run": failing_tool}}}}

    result = run_tool(reg, "test", "fail", {})
    assert result["ok"] is True
    assert call_count == 3


def test_timeout_final_failure():
    """Test timeout wrapper returns structured fallback on final failure"""
    from registry import run_tool
    from core.watchdog import init_watchdog_session

    init_watchdog_session()

    def always_failing_tool():
        raise Exception("Always fails")

    reg = {"test": {"actions": {"fail": {"run": always_failing_tool}}}}

    result = run_tool(reg, "test", "fail", {})
    assert result["ok"] is False
    assert "timeout or failure in test.fail" in result["error"]
    assert "try again or use echo" in result["hint"]


def test_watchdog_disable_after_failures():
    """Test watchdog disables action after 3 failures in 60s"""
    from core.watchdog import ToolWatchdog

    watchdog = ToolWatchdog(failure_threshold=3, time_window=60.0)

    for i in range(3):
        disabled = watchdog.record_failure("test_tool", "test_action")
        if i < 2:
            assert not disabled
        else:
            assert disabled

    assert watchdog.is_disabled("test_tool", "test_action")
    assert (
        "temporarily disabled"
        in watchdog.get_disabled_message("test_tool", "test_action").lower()
    )


def test_watchdog_integration_with_registry():
    """Test watchdog integration with registry run_tool"""
    from registry import run_tool
    from core.watchdog import init_watchdog_session

    init_watchdog_session()

    def failing_tool():
        raise Exception("Simulated failure")

    reg = {"test": {"actions": {"fail": {"run": failing_tool}}}}

    result = run_tool(reg, "test", "fail", {})
    assert "timeout or failure" in result["error"]

    result = run_tool(reg, "test", "fail", {})
    assert "temporarily disabled" in result["error"]


def test_runtime_memory_note_persistence():
    """Test note intent persists to long-term memory"""
    import jarvis
    from unittest.mock import patch

    with patch.object(jarvis, "_speak"), patch.object(jarvis, "_save_mem") as mock_save:

        result = jarvis._handle_note(
            "note My focus niche this week is fitness creators"
        )

        assert "Noted:" in result
        assert "My focus niche this week is fitness creators" in result
        assert mock_save.called


def test_runtime_memory_short_term_buffer():
    """Test short-term buffer stores last 10 turns"""
    from core.runtime import RuntimeMemory

    with tempfile.TemporaryDirectory() as tmpdir:
        runtime_file = Path(tmpdir) / "runtime.json"
        memory = RuntimeMemory(str(runtime_file), max_turns=3)

        for i in range(5):
            memory.add_turn(f"user{i}", f"assistant{i}")

        recent = memory.get_recent_context(10)
        assert len(recent) == 3
        assert recent[0]["user"] == "user2"
        assert recent[-1]["user"] == "user4"


def test_runtime_memory_summarize():
    """Test runtime memory summarization"""
    from core.runtime import RuntimeMemory

    with tempfile.TemporaryDirectory() as tmpdir:
        runtime_file = Path(tmpdir) / "runtime.json"
        memory = RuntimeMemory(str(runtime_file), max_turns=10)

        memory.add_turn("set goal build AI empire", "Goal set")
        memory.add_turn("run websearch query=AI", "Search completed")
        memory.add_turn("note Important insight about market", "Noted")

        summary = memory.summarize_recent_turns(10)
        assert len(summary) <= 3
        assert any("goal" in s.lower() for s in summary)


def test_jarvis_loop_with_flags():
    """Test jarvis loop accepts CLI flags"""
    import jarvis
    from unittest.mock import patch

    with (
        patch.object(jarvis, "_speak"),
        patch("builtins.input", side_effect=["quit"]),
        patch.object(jarvis, "_load_mem"),
        patch.object(jarvis, "_save_mem"),
        patch.object(jarvis, "_append_history"),
    ):

        jarvis.loop(speech_enabled=False, watchdog_enabled=False, log_file="test.log")


def test_speech_queue_disabled():
    """Test speech queue respects enabled flag"""
    from tools.speech import SpeechQueue

    queue = SpeechQueue(enabled=False)
    queue.start()

    queue.enqueue("test message")

    assert queue.queue.empty()
    queue.stop()


def test_watchdog_disabled():
    """Test watchdog respects enabled flag"""
    from core.watchdog import ToolWatchdog

    watchdog = ToolWatchdog()
    watchdog.disable()

    disabled = watchdog.record_failure("test", "action")
    assert not disabled
    assert not watchdog.is_disabled("test", "action")


def test_memory_persistence():
    """Test memory persists across sessions"""
    from core.runtime import RuntimeMemory

    with tempfile.TemporaryDirectory() as tmpdir:
        runtime_file = Path(tmpdir) / "runtime.json"

        memory1 = RuntimeMemory(str(runtime_file))
        memory1.add_turn("user1", "assistant1")

        memory2 = RuntimeMemory(str(runtime_file))
        recent = memory2.get_recent_context(10)
        assert len(recent) == 1
        assert recent[0]["user"] == "user1"


def test_speech_queue_status():
    """Test speech queue status reporting"""
    from tools.speech import init_speech_queue, TOOL_SPEC

    init_speech_queue(enabled=True)

    status_fn = TOOL_SPEC["actions"]["status"]["run"]
    result = status_fn()

    assert result["ok"] is True
    assert "enabled" in result


def test_note_command_integration():
    """Test note command integration in jarvis loop"""
    import jarvis
    from unittest.mock import patch

    original_state = jarvis.STATE.copy()

    try:
        with patch.object(jarvis, "_speak"), patch.object(jarvis, "_save_mem"):

            result = jarvis._handle_note("note Test note for integration")

            assert "Noted: Test note for integration" in result
            assert len(jarvis.STATE.get("notes", [])) > 0

            last_note = jarvis.STATE["notes"][-1]
            assert last_note["note"] == "Test note for integration"
            assert last_note["tag"] == "manual_note"
            assert "ts" in last_note

    finally:
        jarvis.STATE = original_state
