from __future__ import annotations
from pathlib import Path
import os
import tempfile


def _safe_roots() -> list[Path]:
    """Directories considered safe for file operations."""
    roots = [
        Path.cwd().resolve(),
        Path("data").resolve(),
        Path("logs").resolve(),
        Path(tempfile.gettempdir()).resolve(),
    ]
    extra = os.environ.get("UJ_FILES_SAFE_DIRS")
    if extra:
        for p in extra.split(os.pathsep):
            p = p.strip()
            if p:
                try:
                    roots.append(Path(p).expanduser().resolve())
                except Exception:
                    pass
    seen = set()
    unique = []
    for r in roots:
        if r not in seen:
            unique.append(r)
            seen.add(r)
    return unique


def _is_relative_to(child: Path, parent: Path) -> bool:
    """Py3.9-safe helper similar to Path.is_relative_to."""
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def _is_allowed(path: Path) -> bool:
    """Allow if inside any safe root."""
    for root in _safe_roots():
        if _is_relative_to(path, root):
            return True
    return False


def _safe(p: str) -> Path:
    """Resolve a path and enforce protections on sensitive locations."""
    path = Path(p).expanduser().resolve()

    forbidden = {
        Path("/"),
        Path("/System"),
        Path("/bin"),
        Path("/usr"),
        Path("/etc"),
    }

    if str(path).startswith("/tmp/"):
        return path

    if _is_allowed(path):
        return path

    if any(str(path).startswith(str(f)) for f in forbidden):
        raise ValueError("protected path")

    repo_root = Path.cwd().resolve()
    if not _is_relative_to(path, repo_root):
        raise ValueError("path outside allowed roots")

    return path


def read(path: str, head: int = 20, tail: int = 20) -> dict:
    try:
        p = _safe(path)
        if not p.exists():
            return {"ok": False, "error": f"not found: {p}"}
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        prev = (
            lines[:head]
            + (["…"] if len(lines) > head + tail else [])
            + (lines[-tail:] if len(lines) > head else [])
        )
        return {"ok": True, "path": str(p), "lines": len(lines), "preview": prev}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def write(path: str, content: str, confirm: bool = False, backup: bool = True) -> dict:
    """Write content to a file with safety checks."""
    try:
        if not confirm:
            return {
                "ok": False,
                "error": "confirmation required",
                "hint": "pass confirm=True",
            }

        p = _safe(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        if p.exists() and backup:
            backup_path = p.with_suffix(p.suffix + ".bak")
            backup_path.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

        p.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(p), "bytes": len(content)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


TOOL_SPEC = {
    "name": "files",
    "help": "Guarded file I/O with safety protections",
    "actions": {
        "default": {"help": "read file", "run": read},
        "read": {"help": "preview file content", "run": read},
        "write": {"help": "write file (requires confirm=True)", "run": write},
    },
}

__all__ = ["read", "write", "TOOL_SPEC"]
