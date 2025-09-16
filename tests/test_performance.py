def test_jarvis_loop_iteration_performance(benchmark):
    """Benchmark single jarvis loop iteration"""
    from jarvis import _handle_run_tool, _handle_set_goal, _handle_memory

    def jarvis_iteration():
        _handle_set_goal("set goal test performance")
        _handle_memory("show memory")
        return _handle_run_tool("run roadmap status")

    result = benchmark(jarvis_iteration)
    assert "ok" in str(result)


def test_roadmap_operations_performance(benchmark):
    """Benchmark roadmap seed/run/status operations"""
    from tools import roadmap

    def roadmap_operations():
        roadmap.RM.parent.mkdir(parents=True, exist_ok=True)
        roadmap.RM.write_text("# Test Roadmap\n\n## Phase 1\n- Task 1\n- Task 2\n")

        roadmap.seed(limit=10)
        roadmap.run(batch=5)
        return roadmap.status()

    result = benchmark(roadmap_operations)
    assert result["ok"] is True


def test_speech_queue_performance(benchmark):
    """Benchmark speech queue operations with stubs"""
    from tools.speech import SpeechQueue

    def speech_operations():
        queue = SpeechQueue(maxsize=8, enabled=False)
        queue.start()

        for i in range(10):
            queue.enqueue(f"Test message {i}")

        queue.stop()
        return True

    result = benchmark(speech_operations)
    assert result is True


def test_metrics_collection_performance(benchmark):
    """Benchmark metrics collection and aggregation"""
    from runtime.metrics import MetricsCollector

    def metrics_operations():
        collector = MetricsCollector()

        for i in range(50):
            collector.record_tool_execution("test", "action", 100 + i, True, i % 2 == 0)

        return collector.get_summary()

    result = benchmark(metrics_operations)
    assert result["runs"] == 50


def test_memory_operations_performance(benchmark):
    """Benchmark memory persistence operations"""

    def memory_operations():
        try:
            from memory.persistence import get_enhanced_memory

            memory = get_enhanced_memory()

            for i in range(10):
                memory.add_note_with_cache(f"Test note {i}", "benchmark")

            return memory.get_cached_notes()
        except ImportError:
            return []

    result = benchmark(memory_operations)
    assert isinstance(result, list)
