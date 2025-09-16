import time
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest


@pytest.fixture(autouse=True)
def clean_test_state():
    """Clean up shared state before each test"""
    try:
        from core.cache import get_tool_cache

        get_tool_cache().clear()
    except ImportError:
        pass

    try:
        from core.watchdog import init_watchdog_session

        init_watchdog_session()
    except ImportError:
        pass

    yield

    try:
        from core.cache import get_tool_cache

        get_tool_cache().clear()
    except ImportError:
        pass


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

    def failing_tool():
        raise Exception("Simulated failure")

    reg = {"test": {"actions": {"fail": {"run": failing_tool}}}}

    result = run_tool(reg, "test", "fail", {})
    assert result["ok"] is False
    assert "timeout or failure" in result.get("error", "")

    result = run_tool(reg, "test", "fail", {})
    assert "temporarily disabled" in result["error"]


def test_runtime_memory_note_persistence():
    """Test note intent persists to long-term memory"""
    import jarvis
    from unittest.mock import patch

    with patch.object(jarvis, "_speak"):
        result = jarvis._handle_note(
            "note My focus niche this week is fitness creators"
        )

        assert "Noted:" in result
        assert "My focus niche this week is fitness creators" in result


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

    finally:
        jarvis.STATE = original_state


def test_cache_hit_performance():
    """Test caching makes repeat calls faster"""
    from core.cache import ToolCache
    import time

    cache = ToolCache(ttl_seconds=60)

    def slow_function():
        time.sleep(0.1)
        return {"ok": True, "result": "cached_data"}

    start = time.time()
    result1 = slow_function()
    duration1 = time.time() - start
    cache.set("test", "action", {}, result1)

    start = time.time()
    result2 = cache.get("test", "action", {})
    duration2 = time.time() - start

    assert result2 is not None
    assert result2["result"] == "cached_data"
    assert duration2 < duration1 / 10


def test_sqlite_persistence_across_restart():
    """Test SQLite persistence survives restart"""
    from core.persistence import PersistentMemory
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"

        memory1 = PersistentMemory(str(db_path))
        success = memory1.add_note("Test persistent note", "test_tag")
        assert success

        memory2 = PersistentMemory(str(db_path))
        notes = memory2.get_notes(limit=10)
        assert len(notes) == 1
        assert notes[0]["note"] == "Test persistent note"
        assert notes[0]["tag"] == "test_tag"


def test_profile_output_correctness():
    """Test --profile flag outputs correct timing data"""
    from registry import enable_profiling, get_profile_data, disable_profiling, run_tool
    import time

    enable_profiling()

    def mock_tool():
        time.sleep(0.01)
        return {"ok": True}

    reg = {"test": {"actions": {"action": {"run": mock_tool}}}}

    run_tool(reg, "test", "action", {})
    run_tool(reg, "test", "action", {})

    stats = get_profile_data()
    assert "test.action" in stats
    assert stats["test.action"]["calls"] == 2
    assert stats["test.action"]["total_time"] > 0.01

    disable_profiling()


def test_forget_last_functionality():
    """Test --forget-last clears recent conversation"""
    from core.persistence import PersistentMemory
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"
        memory = PersistentMemory(str(db_path))

        memory.add_conversation("user1", "assistant1")
        memory.add_conversation("user2", "assistant2")

        conversations = memory.get_conversations()
        assert len(conversations) == 2

        success = memory.clear_last_conversation()
        assert success

        conversations = memory.get_conversations()
        assert len(conversations) == 1
        assert conversations[0]["user"] == "user1"


def test_clear_memory_functionality():
    """Test --clear-memory clears all data"""
    from core.persistence import PersistentMemory
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"
        memory = PersistentMemory(str(db_path))

        memory.add_note("Test note")
        memory.add_conversation("user", "assistant")

        notes = memory.get_notes()
        conversations = memory.get_conversations()
        assert len(notes) == 1
        assert len(conversations) == 1

        success = memory.clear_all_memory()
        assert success

        notes = memory.get_notes()
        conversations = memory.get_conversations()
        assert len(notes) == 0
        assert len(conversations) == 0


def test_memory_search_functionality():
    """Test memory search functionality"""
    from core.persistence import PersistentMemory
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_memory.db"
        memory = PersistentMemory(str(db_path))

        memory.add_note("AI empire building strategy")
        memory.add_note("Fitness creator content ideas")
        memory.add_note("Marketing automation tools")

        results = memory.search_notes("AI")
        assert len(results) == 1
        assert "AI empire" in results[0]["note"]

        results = memory.search_notes("fitness")
        assert len(results) == 1
        assert "Fitness creator" in results[0]["note"]

        results = memory.search_notes("nonexistent")
        assert len(results) == 0


def test_cache_ttl_expiration():
    """Test cache TTL expiration works correctly"""
    from core.cache import ToolCache
    import time

    cache = ToolCache(ttl_seconds=0.1)

    cache.set("test", "action", {}, {"ok": True, "data": "test"})

    result = cache.get("test", "action", {})
    assert result is not None

    time.sleep(0.2)

    result = cache.get("test", "action", {})
    assert result is None


def test_cache_max_size_eviction():
    """Test cache evicts oldest entries when max size reached"""
    from core.cache import ToolCache

    cache = ToolCache(max_size=2)

    cache.set("test", "action1", {}, {"data": "1"})
    cache.set("test", "action2", {}, {"data": "2"})
    cache.set("test", "action3", {}, {"data": "3"})

    assert cache.get("test", "action1", {}) is None
    assert cache.get("test", "action2", {}) is not None
    assert cache.get("test", "action3", {}) is not None


def test_metrics_aggregation():
    """Test metrics collection and aggregation"""
    from runtime.metrics import MetricsCollector

    collector = MetricsCollector()

    collector.record_tool_execution("test", "action", 100, True, False)
    collector.record_tool_execution("test", "action", 200, False, True)

    summary = collector.get_summary()
    assert summary["runs"] == 2
    assert summary["fails"] == 1
    assert summary["cache_hits"] == 1
    assert summary["cache_misses"] == 1
    assert "test.action" in summary["avg_ms_by_tool"]
    assert summary["avg_ms_by_tool"]["test.action"] == 150.0


def test_lru_cache_behavior():
    """Test LRU cache eviction and TTL"""
    from memory.lru import LRUCache
    import time

    cache = LRUCache(capacity=2, ttl_seconds=1)

    cache.put("key1", "value1")
    cache.put("key2", "value2")
    cache.put("key3", "value3")

    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"

    time.sleep(1.1)
    assert cache.get("key2") is None
    assert cache.get("key3") is None


def test_structured_logging_output():
    """Test JSON logging format"""
    import json
    import tempfile
    import logging
    from runtime.loggingx import setup_structured_logging

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".log", delete=False) as f:
        setup_structured_logging(f.name)
        logger = logging.getLogger()
        logger.info(
            "test message",
            extra={
                "tool": "test.action",
                "duration_ms": 100,
                "result": "ok",
                "cache_hit": True,
            },
        )

        f.seek(0)
        log_line = f.readline().strip()
        log_data = json.loads(log_line)

        assert "timestamp" in log_data
        assert log_data["level"] == "INFO"
        assert log_data["tool"] == "test.action"
        assert log_data["duration_ms"] == 100
        assert log_data["result"] == "ok"
        assert log_data["cache_hit"] is True


def test_enhanced_memory_commands():
    """Test enhanced memory command tracking"""
    import tempfile
    import os
    from memory.persistence import EnhancedMemory

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, "test_memory.db")
        memory = EnhancedMemory(db_path=test_db)
        memory.add_command("note", "test note", True, 50)
        memory.add_command("search", "test query", False, 100)

        commands = memory.get_recent_commands(limit=5)
        assert len(commands) == 2
        assert commands[0]["intent"] == "search"
        assert commands[0]["success"] is False
        assert commands[1]["intent"] == "note"
        assert commands[1]["success"] is True


def test_memory_view_command():
    """Test memory view CLI command functionality"""
    import tempfile
    import os
    from memory.persistence import EnhancedMemory
    from memory.lru import reset_note_cache

    reset_note_cache()

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, "test_memory.db")
        memory = EnhancedMemory(db_path=test_db)
        memory.add_note_with_cache("test note", "manual_note")
        memory.add_command("note", "note test note", True, 25)

        notes = memory.persistence.get_notes(limit=50)
        cached_notes = memory.get_cached_notes()
        commands = memory.get_recent_commands(limit=10)

        assert len(notes) == 1
        assert notes[0]["note"] == "test note"
        assert len(cached_notes) == 1
        assert len(commands) == 1


def test_enhanced_metrics_percentiles():
    """Test enhanced metrics with percentile calculation"""
    from runtime.metrics import MetricsCollector

    collector = MetricsCollector()

    latencies = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    for i, latency in enumerate(latencies):
        collector.record_tool_execution("test", "action", latency, True, False)

    summary = collector.get_summary()

    assert "overall_latency_p50" in summary
    assert "overall_latency_p95" in summary
    assert "error_rate_percent" in summary
    assert summary["overall_latency_p50"] == 55.0
    assert summary["error_rate_percent"] == 0.0


def test_performance_test_structure():
    """Test that performance tests are properly structured"""
    import tests.test_performance

    assert hasattr(tests.test_performance, "test_jarvis_loop_iteration_performance")
    assert hasattr(tests.test_performance, "test_roadmap_operations_performance")
    assert hasattr(tests.test_performance, "test_speech_queue_performance")


def test_metrics_error_rate_calculation():
    """Test error rate calculation in enhanced metrics"""
    from runtime.metrics import MetricsCollector

    collector = MetricsCollector()

    collector.record_tool_execution("test", "action", 100, True, False)
    collector.record_tool_execution("test", "action", 200, False, False)
    collector.record_tool_execution("test", "action", 150, True, False)
    collector.record_tool_execution("test", "action", 300, False, False)

    summary = collector.get_summary()

    assert summary["runs"] == 4
    assert summary["fails"] == 2
    assert summary["error_rate_percent"] == 50.0
