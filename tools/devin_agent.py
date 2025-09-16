import os
import json
import subprocess
import tempfile
import shutil
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

MAX_FILES = int(os.getenv("UJ_DEVIN_MAX_FILES", "5"))
MAX_LINES = int(os.getenv("UJ_DEVIN_MAX_LINES", "400"))
RETRIES = int(os.getenv("UJ_DEVIN_RETRIES", "1"))
ENABLED = os.getenv("UJ_DEVIN_ENABLED", "0") == "1"
FAKE_MODE = os.getenv("UJ_DEVIN_FAKE", "0") == "1"
SANDBOX_MODE = os.getenv("UJ_DEVIN_SANDBOX", "0") == "1"
OPEN_PR = os.getenv("UJ_DEVIN_OPEN_PR", "0") == "1"

PROTECTED_PATHS = [
    ".github/workflows/*", "pyproject.toml", "setup.py", "MANIFEST.in",
    ".git/*", ".venv/*", "ultra_jarvis.egg-info/*"
]


def devin_agent(task: str) -> Dict[str, Any]:
    """Main devin agent entry point"""
    if not ENABLED:
        return {"ok": False, "error": "Devin agent not enabled. Set UJ_DEVIN_ENABLED=1"}
    
    start_time = datetime.utcnow()
    run_log = {
        "ts": start_time.isoformat() + "Z",
        "task": task,
        "mode": "fake" if FAKE_MODE else "real",
        "branch": None,
        "changed_files": [],
        "lint_ok": False,
        "tests_ok": False,
        "committed": False,
        "errors": [],
        "duration_s": 0
    }
    
    try:
        if FAKE_MODE:
            return _handle_fake_mode(task, run_log)
        else:
            return _handle_real_mode(task, run_log)
    except Exception as e:
        run_log["errors"].append(str(e))
        return {"ok": False, "error": str(e), "run_log": run_log}
    finally:
        run_log["duration_s"] = (datetime.utcnow() - start_time).total_seconds()
        _log_run(run_log)


def _handle_fake_mode(task: str, run_log: Dict) -> Dict[str, Any]:
    """Handle fake mode for testing"""
    if task.lower() == "demo":
        branch_name = f"devin/demo-{int(datetime.utcnow().timestamp())}"
        run_log.update({
            "branch": branch_name,
            "changed_files": ["demo_file.py"],
            "lint_ok": True,
            "tests_ok": True,
            "committed": True
        })
        return {
            "ok": True,
            "message": f"Fake mode: would create branch {branch_name}",
            "run_log": run_log
        }
    
    plan = {"files": [{"path": "example.py", "action": "modify", "reason": "fake change"}]}
    run_log["changed_files"] = ["example.py"]
    
    return {
        "ok": True,
        "message": f"Fake mode: would execute task '{task}'",
        "plan": plan,
        "run_log": run_log
    }


def _handle_real_mode(task: str, run_log: Dict) -> Dict[str, Any]:
    """Handle real mode implementation"""
    plan = _create_plan(task)
    if not plan.get("ok"):
        run_log["errors"].append("Planning failed")
        return plan
    
    branch_name = _create_branch(task)
    run_log["branch"] = branch_name
    
    changed_files = []
    for file_spec in plan["files"]:
        result = _apply_patch(file_spec, run_log)
        if result.get("ok"):
            changed_files.append(file_spec["path"])
        else:
            run_log["errors"].append(f"Patch failed for {file_spec['path']}")
    
    run_log["changed_files"] = changed_files
    
    if changed_files:
        run_log["lint_ok"] = _run_lint()
        run_log["tests_ok"] = _run_tests()
        
        if run_log["lint_ok"] and run_log["tests_ok"]:
            run_log["committed"] = _commit_and_push(branch_name, task, changed_files)
            
            if OPEN_PR and run_log["committed"]:
                _create_pr(branch_name, task)
    
    return {
        "ok": len(changed_files) > 0 and run_log["committed"],
        "plan": plan,
        "changed_files": changed_files,
        "run_log": run_log
    }


def _create_plan(task: str) -> Dict[str, Any]:
    """Create execution plan using cloud AI"""
    try:
        from cloud_bridge import ask_cloud_ai
        
        prompt = f"""
        Create a JSON plan for this task: {task}
        
        Return only valid JSON in this format:
        {{"files": [{{"path": "relative/path.py", "action": "modify|create|delete", "reason": "brief reason"}}]}}
        
        Limit to {MAX_FILES} files maximum.
        Focus on minimal, targeted changes.
        """
        
        response = ask_cloud_ai(prompt)
        plan = json.loads(response.strip())
        
        if len(plan.get("files", [])) > MAX_FILES:
            return {"ok": False, "error": f"Plan exceeds {MAX_FILES} file limit"}
        
        return {"ok": True, **plan}
    except Exception as e:
        return {"ok": False, "error": f"Planning failed: {e}"}


def _create_branch(task: str) -> str:
    """Create a new git branch for the task"""
    timestamp = int(datetime.utcnow().timestamp())
    task_slug = re.sub(r'[^a-z0-9]+', '-', task.lower())[:30]
    branch_name = f"devin/{timestamp}-{task_slug}"
    
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    return branch_name


def _apply_patch(file_spec: Dict, run_log: Dict) -> Dict[str, Any]:
    """Apply a patch for a single file"""
    file_path = file_spec["path"]
    
    if _is_protected_path(file_path):
        return {"ok": False, "error": f"Protected path: {file_path}"}
    
    _create_backup(file_path)
    
    try:
        from cloud_bridge import ask_cloud_ai
        
        if file_spec["action"] == "create":
            prompt = f"""
            Create new file content for: {file_path}
            Task: {file_spec['reason']}
            
            Return only the file content, no markdown fences.
            """
            content = ask_cloud_ai(prompt)
            
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(file_path).write_text(content)
            
        elif file_spec["action"] == "modify":
            current_content = Path(file_path).read_text() if Path(file_path).exists() else ""
            
            prompt = f"""
            Modify this file: {file_path}
            Current content:
            {current_content}
            
            Task: {file_spec['reason']}
            
            Return a unified diff in format:
            diff --git a/{file_path} b/{file_path}
            index abc123..def456 100644
            --- a/{file_path}
            +++ b/{file_path}
            @@ -1,3 +1,3 @@
             line1
            -old line
            +new line
             line3
            """
            
            diff_content = ask_cloud_ai(prompt)
            
            if not diff_content.startswith("diff --git"):
                diff_content = _wrap_raw_content_to_diff(file_path, diff_content, is_new=False)
            
            _apply_unified_diff(diff_content)
        
        elif file_spec["action"] == "delete":
            if Path(file_path).exists():
                Path(file_path).unlink()
        
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _is_protected_path(path: str) -> bool:
    """Check if path is protected"""
    for pattern in PROTECTED_PATHS:
        if pattern.endswith("*"):
            if path.startswith(pattern[:-1]):
                return True
        elif path == pattern:
            return True
    return False


def _create_backup(file_path: str):
    """Create backup of file before modification"""
    if not Path(file_path).exists():
        return
    
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{Path(file_path).name}_{timestamp}.bak"
    shutil.copy2(file_path, backup_path)


def _wrap_raw_content_to_diff(file_path: str, content: str, is_new: bool) -> str:
    """Wrap raw content into a unified diff format"""
    if is_new:
        return f"""diff --git a/{file_path} b/{file_path}
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/{file_path}
@@ -0,0 +1,{len(content.splitlines())} @@
{chr(10).join('+' + line for line in content.splitlines())}
"""
    else:
        old_content = Path(file_path).read_text() if Path(file_path).exists() else ""
        old_lines = old_content.splitlines()
        new_lines = content.splitlines()
        
        return f"""diff --git a/{file_path} b/{file_path}
index abc123..def456 100644
--- a/{file_path}
+++ b/{file_path}
@@ -1,{len(old_lines)} +1,{len(new_lines)} @@
{chr(10).join('-' + line for line in old_lines)}
{chr(10).join('+' + line for line in new_lines)}
"""


def _apply_unified_diff(diff_content: str):
    """Apply a unified diff using git apply"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
        f.write(diff_content)
        patch_file = f.name
    
    try:
        subprocess.run(["git", "apply", patch_file], check=True)
    finally:
        Path(patch_file).unlink()


def _run_lint() -> bool:
    """Run ruff linting"""
    try:
        result = subprocess.run(["ruff", "check", "."], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False


def _run_tests() -> bool:
    """Run pytest"""
    try:
        result = subprocess.run(["pytest", "-q"], capture_output=True)
        return result.returncode == 0
    except Exception:
        return False


def _commit_and_push(branch_name: str, task: str, changed_files: List[str]) -> bool:
    """Commit and push changes"""
    try:
        for file_path in changed_files:
            subprocess.run(["git", "add", file_path], check=True)
        
        commit_msg = f"devin: {task}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", branch_name], check=True)
        return True
    except Exception:
        return False


def _create_pr(branch_name: str, task: str):
    """Create a pull request using gh CLI"""
    try:
        subprocess.run([
            "gh", "pr", "create",
            "--title", f"Devin: {task}",
            "--body", f"Automated changes for: {task}",
            "--head", branch_name,
            "--base", "main"
        ], check=True)
    except Exception:
        pass


def _log_run(run_log: Dict):
    """Log run to devin_runs.jsonl"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "devin_runs.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(run_log) + "\n")


TOOL_SPEC = {
    "name": "devin_agent",
    "help": "Production-grade developer agent",
    "actions": {
        "devin": {"help": "Execute natural language task", "run": devin_agent}
    }
}
