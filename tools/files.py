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
        Path(tempfile.gettempdir()).resolve(),  # system tmp (macOS/Linux/Windows)
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
    # de-duplicate while preserving order
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

    # Hard-forbidden top-level system directories
    forbidden = {
        Path("/"),
        Path("/System"),
        Path("/bin"),
        Path("/usr"),
        Path("/etc"),
    }

    # If it's in a safe root, allow
    if _is_allowed(path):
        return path

    # Otherwise, block if it’s under any forbidden root
    if any(str(path).startswith(str(f)) for f in forbidden):
        raise ValueError("protected path")

    # Default: allow paths within the repo (already covered) or user-specified safe dirs
    # Anything else falls through as 'not explicitly forbidden' (still outside safe roots)
    # To be conservative, require it to be in the repo tree.
    repo_root = Path.cwd().resolve()
    if not _is_relative_to(path, repo_root):
        raise ValueError("path outside allowed roots")

def _safe(p: str) -> Path:
    path = Path(p).expanduser().resolve()
    forbidden = {Path("/"), Path("/System"), Path("/bin"), Path("/usr"), Path("/etc")}
    # block system paths, but allow /tmp for testing
    if any(str(path).startswith(str(f)) for f in forbidden) and not str(path).startswith("/tmp/"):
        raise ValueError("protected path")
    return path
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


def _safe(p: str) -> Path:
    path = Path(p).expanduser().resolve()
    forbidden = {Path("/"), Path("/System"), Path("/bin"), Path("/usr"), Path("/etc")}
    # block system paths, but allow /tmp for testing
    if any(str(path).startswith(str(f)) for f in forbidden) and not str(path).startswith("/tmp/"):
        raise ValueError("protected path")
    return path
