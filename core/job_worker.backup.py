import json
import time
from pathlib import Path
from core.natural_tasks import NaturalTaskRunner

QUEUE = Path("workspace/queue.jsonl")
DONE = Path("workspace/done.jsonl")
QUEUE.parent.mkdir(parents=True, exist_ok=True)


def enqueue(prompt, output_dir=None):
    with open(QUEUE, "a") as f:
        f.write(
            json.dumps({"prompt": prompt, "output_dir": output_dir, "ts": time.time()})
            + "\n"
        )


def run_forever(sleep_sec=3):
    runner = NaturalTaskRunner()
    while True:
        if not QUEUE.exists():
            time.sleep(sleep_sec)
            continue
        lines = QUEUE.read_text().splitlines()
        if not lines:
            time.sleep(sleep_sec)
            continue
        head, rest = lines[0], lines[1:]
        QUEUE.write_text("\n".join(rest))
        job = json.loads(head)
        try:
            res = runner.build_and_run(job["prompt"], job.get("output_dir"))
            rec = {"ok": True, "job": job, "res": res, "ts_done": time.time()}
        except Exception as e:
            rec = {"ok": False, "job": job, "err": str(e), "ts_done": time.time()}
        with open(DONE, "a") as f:
            f.write(json.dumps(rec) + "\n")
