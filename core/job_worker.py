# core/job_worker.py
import json, time
from pathlib import Path
from typing import Optional, Union

QUEUE = Path("workspace/queue.jsonl")
DONE = Path("workspace/done.jsonl")
QUEUE.parent.mkdir(parents=True, exist_ok=True)


def enqueue(prompt: str, *, output_dir: str | None = None):
    rec = {"prompt": prompt, "output_dir": output_dir, "ts": time.time()}
    with open(QUEUE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _read_one() -> Optional[Union[str, dict]]:
    """Read first non-empty line from queue; return dict or sentinels."""
    if not QUEUE.exists():
        return None
    lines = QUEUE.read_text(encoding="utf-8").splitlines()
    if not lines:
        return None
    head, rest = lines[0], "\n".join(lines[1:])
    QUEUE.write_text(rest, encoding="utf-8")
    head = head.strip()
    if not head:
        return "__EMPTY__"
    try:
        return json.loads(head)
    except Exception:
        # log the bad line and continue
        DONE.parent.mkdir(parents=True, exist_ok=True)
        with open(DONE.with_name("bad_queue.jsonl"), "a", encoding="utf-8") as bf:
            bf.write(head + "\n")
        return "__BAD__"


def run_forever(sleep_sec: int = 3):
    """Main worker loop."""
    # Import here so enqueue callers don’t need natural_tasks.
    from core.natural_tasks import NaturalTaskRunner

    runner = NaturalTaskRunner()
    while True:
        rec = _read_one()
        if rec is None:
            time.sleep(sleep_sec)
            continue
        if rec in ("__EMPTY__", "__BAD__"):
            continue
        try:
            out = runner.build_and_run(rec["prompt"], rec.get("output_dir"))
            with open(DONE, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {"ok": True, "job": rec, "ts_done": time.time()},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except Exception as e:
            with open(DONE, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "ok": False,
                            "job": rec,
                            "err": str(e),
                            "ts_done": time.time(),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )


__all__ = ["enqueue", "run_forever"]
