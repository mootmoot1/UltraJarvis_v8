import subprocess
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def run_quality_checks() -> Dict[str, Any]:
    """Run all quality checks: ruff, black, pytest"""
    results = {"success": True, "errors": [], "checks": {}}

    ruff_result = run_ruff_check()
    results["checks"]["ruff"] = ruff_result
    if not ruff_result["success"]:
        results["success"] = False
        results["errors"].extend(ruff_result["errors"])

    black_result = run_black_check()
    results["checks"]["black"] = black_result
    if not black_result["success"]:
        results["success"] = False
        results["errors"].extend(black_result["errors"])

    pytest_result = run_pytest()
    results["checks"]["pytest"] = pytest_result
    if not pytest_result["success"]:
        results["success"] = False
        results["errors"].extend(pytest_result["errors"])

    return results


def run_ruff_check() -> Dict[str, Any]:
    """Run ruff linting"""
    try:
        result = subprocess.run(
            ["ruff", "check", "."], capture_output=True, text=True, timeout=60
        )

        if result.returncode == 0:
            return {"success": True, "errors": []}
        else:
            errors = result.stdout.split("\n") if result.stdout else []
            errors.extend(result.stderr.split("\n") if result.stderr else [])
            errors = [e.strip() for e in errors if e.strip()]

            return {"success": False, "errors": errors}

    except subprocess.TimeoutExpired:
        return {"success": False, "errors": ["Ruff check timed out"]}
    except Exception as e:
        return {"success": False, "errors": [f"Ruff check failed: {e}"]}


def run_black_check() -> Dict[str, Any]:
    """Run black formatting check"""
    try:
        result = subprocess.run(
            ["black", "--check", "."], capture_output=True, text=True, timeout=60
        )

        if result.returncode == 0:
            return {"success": True, "errors": []}
        else:
            errors = result.stdout.split("\n") if result.stdout else []
            errors.extend(result.stderr.split("\n") if result.stderr else [])
            errors = [e.strip() for e in errors if e.strip()]

            return {"success": False, "errors": errors}

    except subprocess.TimeoutExpired:
        return {"success": False, "errors": ["Black check timed out"]}
    except Exception as e:
        return {"success": False, "errors": [f"Black check failed: {e}"]}


def run_pytest() -> Dict[str, Any]:
    """Run pytest"""
    try:
        result = subprocess.run(
            ["pytest", "-q"], capture_output=True, text=True, timeout=120
        )

        if result.returncode == 0:
            return {"success": True, "errors": []}
        else:
            errors = result.stdout.split("\n") if result.stdout else []
            errors.extend(result.stderr.split("\n") if result.stderr else [])
            errors = [e.strip() for e in errors if e.strip()]

            return {"success": False, "errors": errors}

    except subprocess.TimeoutExpired:
        return {"success": False, "errors": ["Pytest timed out"]}
    except Exception as e:
        return {"success": False, "errors": [f"Pytest failed: {e}"]}
