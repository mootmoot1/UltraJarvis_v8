import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_natural_task_runner_import():
    """Test that NaturalTaskRunner can be imported"""
    from core.natural_tasks import NaturalTaskRunner

    runner = NaturalTaskRunner()
    assert runner is not None


def test_job_worker_import():
    """Test that job_worker module can be imported"""
    import core.job_worker as jw

    assert hasattr(jw, "enqueue")
    assert hasattr(jw, "run_forever")


def test_job_worker_enqueue():
    """Test job worker enqueue functionality"""
    import core.job_worker as jw

    with patch("cloud_bridge.ask_cloud_ai") as mock_cloud:
        mock_cloud.return_value = "No files to create"

        result = jw.enqueue("Test task")
        assert result is True


def test_natural_task_runner_basic():
    """Test NaturalTaskRunner basic functionality"""
    from core.natural_tasks import NaturalTaskRunner

    with tempfile.TemporaryDirectory() as tmp_dir:
        runner = NaturalTaskRunner()

        with patch.object(runner, "_call_cloud_bridge") as mock_cloud:
            mock_cloud.return_value = """<<<FILES
docs/test.md
Hello World
<<<FILES OK"""

            with patch("core.quality.run_quality_checks") as mock_quality:
                mock_quality.return_value = {"success": True, "errors": []}

                result = runner.build_and_run("Create test file", tmp_dir)

                assert result["ok"] is True
                assert len(result["written_files"]) > 0


def test_worker_smoke_integration():
    """Smoke test for worker integration"""
    import core.job_worker as jw

    worker = jw.init_worker()
    assert worker is not None

    worker.start()
    time.sleep(0.1)
    worker.stop()
