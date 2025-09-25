import pytest
from core.logger import setup_logger, log_job


@pytest.fixture(autouse=True)
def run_around_tests():
    setup_logger()
    yield


def test_log_job(caplog):
    log_job("test_job", "hash123", ["file1.py", "file2.py"], "summary", "result")
    assert "Job: test_job" in caplog.text
    assert "Prompt Hash: hash123" in caplog.text
    assert "Files Written: [" in caplog.text
