from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path


class JSONLineFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }

        if hasattr(record, "tool"):
            log_entry["tool"] = record.tool
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "result"):
            log_entry["result"] = record.result
        if hasattr(record, "cache_hit"):
            log_entry["cache_hit"] = record.cache_hit

        return json.dumps(log_entry)


def setup_structured_logging(log_file: str = "logs/uj.log"):
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(JSONLineFormatter())
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)
