import queue
import threading
import logging
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from .natural_tasks import NaturalTaskRunner

logger = logging.getLogger(__name__)


class JobWorker:
    def __init__(self, maxsize: int = 10):
        self.queue = queue.Queue(maxsize=maxsize)
        self.worker_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        self.running = False

    def start(self):
        """Start the worker thread"""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.shutdown_event.clear()
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
            logger.info("Job worker started")

    def stop(self):
        """Stop the worker thread"""
        self.running = False
        self.shutdown_event.set()
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        logger.info("Job worker stopped")

    def enqueue_job(self, prompt: str, output_dir: str = "workspace") -> bool:
        """Enqueue a job for processing"""
        job = {
            "id": f"job_{int(time.time())}_{id(self)}",
            "prompt": prompt,
            "output_dir": output_dir,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

        try:
            self.queue.put_nowait(job)
            logger.info(f"Enqueued job: {job['id']}")
            return True
        except queue.Full:
            logger.warning("Job queue is full, dropping job")
            return False

    def _worker(self):
        """Main worker loop"""
        logger.info("Job worker thread started")

        while not self.shutdown_event.is_set():
            try:
                job = self.queue.get(timeout=1.0)
                self._process_job(job)
                self.queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Job worker error: {e}")

    def _process_job(self, job: Dict[str, Any]):
        """Process a single job"""
        job_id = job["id"]
        prompt = job["prompt"]
        output_dir = job["output_dir"]

        logger.info(f"Processing job {job_id}: {prompt[:50]}...")

        try:
            job_output_dir = Path(output_dir) / job_id
            job_output_dir.mkdir(parents=True, exist_ok=True)

            runner = NaturalTaskRunner()
            result = runner.build_and_run(prompt, str(job_output_dir))

            if result["ok"]:
                logger.info(f"Job {job_id} completed successfully")
                logger.info(f"Files written: {len(result.get('written_files', []))}")
            else:
                logger.error(
                    f"Job {job_id} failed: {result.get('error', 'Unknown error')}"
                )

        except Exception as e:
            logger.error(f"Failed to process job {job_id}: {e}")


_global_worker: Optional[JobWorker] = None


def init_worker() -> JobWorker:
    """Initialize global worker instance"""
    global _global_worker
    if _global_worker is not None:
        _global_worker.stop()
    _global_worker = JobWorker()
    return _global_worker


def enqueue(prompt: str, output_dir: str = "workspace") -> bool:
    """Enqueue a job (public API)"""
    global _global_worker
    if _global_worker is None:
        _global_worker = init_worker()
        _global_worker.start()

    return _global_worker.enqueue_job(prompt, output_dir)


def run_forever():
    """Run worker forever (for bin/uj-worker)"""
    global _global_worker
    if _global_worker is None:
        _global_worker = init_worker()

    _global_worker.start()

    try:
        logger.info("Job worker running forever. Press Ctrl+C to stop.")
        while _global_worker.running:
            time.sleep(1.0)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        _global_worker.stop()


def shutdown_worker():
    """Shutdown global worker"""
    global _global_worker
    if _global_worker is not None:
        _global_worker.stop()
        _global_worker = None
