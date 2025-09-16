import subprocess
import json
import pytest
from unittest.mock import patch, MagicMock


def test_metrics_appears_in_cli_help():
    """Test that 'metrics' appears in CLI help output"""
    result = subprocess.run(
        ["python", "-m", "uc", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "metrics" in result.stdout
    assert (
        "{tools,status,seed,run,add,expand,phase,validate,health,track,jarvis,metrics,memory}"
        in result.stdout
    )


def test_metrics_command_executes():
    """Test that 'uj metrics' command executes without error"""
    result = subprocess.run(
        ["python", "-m", "uc", "metrics"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip() != ""

    output_lines = result.stdout.strip().split("\n")

    json_lines = []
    for line in output_lines:
        if line.strip().startswith("Quick Summary:"):
            break
        json_lines.append(line)

    json_text = "\n".join(json_lines).strip()

    try:
        data = json.loads(json_text)
        assert isinstance(data, dict)
        expected_keys = [
            "runs",
            "fails",
            "error_rate_percent",
            "cache_hits",
            "cache_misses",
        ]
        for key in expected_keys:
            assert key in data
    except json.JSONDecodeError:
        pytest.fail(f"JSON portion of output is not valid: {json_text}")


@patch("runtime.metrics.get_metrics_collector")
def test_metrics_command_with_mock(mock_get_collector):
    """Test metrics command with mocked collector to avoid heavy operations"""
    mock_collector = MagicMock()
    mock_collector.get_summary.return_value = {
        "runs": 10,
        "fails": 1,
        "error_rate_percent": 10.0,
        "cache_hits": 5,
        "cache_misses": 5,
        "avg_ms_by_tool": {"test_tool": 50.0},
        "percentiles_by_tool": {"test_tool": {"p50": 45.0, "p95": 75.0}},
        "overall_latency_p50": 45.0,
        "overall_latency_p95": 75.0,
        "uptime_seconds": 3600,
    }
    mock_get_collector.return_value = mock_collector

    result = subprocess.run(
        ["python", "-m", "uc", "metrics"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "runs" in result.stdout
    assert "Quick Summary:" in result.stdout


def test_metrics_command_imports():
    """Test that metrics command can import required modules"""
    try:
        from runtime.metrics import get_metrics_collector
        from uc import cmd_metrics

        assert callable(cmd_metrics)
        assert callable(get_metrics_collector)
    except ImportError as e:
        pytest.fail(f"Failed to import required modules: {e}")


def test_metrics_subparser_wiring():
    """Test that metrics subparser is properly wired in argparse"""
    import argparse

    ap = argparse.ArgumentParser(prog="uc", description="UltraJarvis v8")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("metrics")

    args = ap.parse_args(["metrics"])
    assert args.cmd == "metrics"
