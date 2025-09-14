from __future__ import annotations
import queue
import threading
import subprocess
import platform
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SpeechQueue:
    def __init__(self, maxsize: int = 8, timeout: float = 10.0, enabled: bool = True):
        self.queue = queue.Queue(maxsize=maxsize)
        self.timeout = timeout
        self.enabled = enabled
        self.worker_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        
    def start(self):
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.shutdown_event.clear()
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
            
    def stop(self):
        self.shutdown_event.set()
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)
            
    def enqueue(self, text: str):
        if not self.enabled:
            return
            
        try:
            self.queue.put_nowait(text)
        except queue.Full:
            try:
                self.queue.get_nowait()
                logger.warning("Speech queue full, dropped oldest message")
            except queue.Empty:
                pass
            try:
                self.queue.put_nowait(text)
            except queue.Full:
                logger.warning("Failed to enqueue speech after dropping oldest")
                
    def _worker(self):
        while not self.shutdown_event.is_set():
            try:
                text = self.queue.get(timeout=0.1)
                self._speak_with_timeout(text)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Speech worker error: {e}")
                
    def _speak_with_timeout(self, text: str):
        if platform.system().lower() == "darwin":
            try:
                proc = subprocess.Popen(["say", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                proc.wait(timeout=self.timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                logger.warning(f"TTS timeout after {self.timeout}s for: {text[:50]}...")
            except Exception as e:
                logger.error(f"TTS error: {e}")

_global_queue: Optional[SpeechQueue] = None

def init_speech_queue(enabled: bool = True) -> SpeechQueue:
    global _global_queue
    if _global_queue is not None:
        _global_queue.stop()
    _global_queue = SpeechQueue(enabled=enabled)
    _global_queue.start()
    return _global_queue

def speak(text: str):
    global _global_queue
    if _global_queue is None:
        _global_queue = init_speech_queue()
    _global_queue.enqueue(text)

def shutdown_speech():
    global _global_queue
    if _global_queue is not None:
        _global_queue.stop()
        _global_queue = None

TOOL_SPEC = {
    "name": "speech",
    "help": "Text-to-speech with queuing",
    "actions": {
        "speak": {"help": "speak text", "run": lambda text="": speak(text)},
        "status": {"help": "queue status", "run": lambda: {"ok": True, "enabled": _global_queue.enabled if _global_queue else False}}
    }
}
