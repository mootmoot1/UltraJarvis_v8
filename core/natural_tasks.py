def write_task(task: str) -> None:
    """Writes a task to the allowed directories."""
    allowed_dirs = ["docs", "core", "tests"]
    if any(dir in task for dir in allowed_dirs):
        with open(f"{task}.txt", "w") as f:
            f.write(task)
    else:
        raise ValueError("Task not in allowed directories.")
