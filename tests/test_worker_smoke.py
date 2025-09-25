import importlib


def test_job_worker_exports():
    jw = importlib.import_module("core.job_worker")
    assert hasattr(jw, "enqueue")
    assert hasattr(jw, "run_forever")


# This is the real bug Devin must fix:
# The worker should be able to start without import errors, and process a trivial job.
def test_worker_smoke_flow(tmp_path, monkeypatch):
    # queue a tiny job
    jw = importlib.import_module("core.job_worker")
    jw.enqueue("Create docs/SMOKE_CI.md with hello")
    # Try to import the runner class; must exist and be usable by run_forever()
    nt = importlib.import_module("core.natural_tasks")
    assert hasattr(
        nt, "NaturalTaskRunner"
    ), "NaturalTaskRunner missing in core.natural_tasks"
