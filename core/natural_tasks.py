import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

ALLOWED_FILES = {
    "docs",
    "core",
    "tests",
    "tools",
    "bin",
    "pyproject.toml",
    "pytest.ini",
    "README.md",
    "requirements.txt",
}


class NaturalTaskRunner:
    def __init__(self):
        self.written_files = []

    def build_and_run(self, prompt: str, output_dir: str) -> Dict[str, Any]:
        """
        Main entry point for natural task execution.
        Calls cloud bridge, parses response, writes files, runs quality gates.
        """
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            response = self._call_cloud_bridge(prompt)

            files_data = self._parse_files_response(response)

            self._write_files(files_data, output_dir)

            quality_result = self._run_quality_gates()

            if not quality_result["success"]:
                logger.info("Quality gates failed, running critic pass...")
                critic_result = self._run_critic_pass(quality_result["errors"])
                if critic_result["success"]:
                    quality_result = self._run_quality_gates()

            self._write_output_files(output_dir)

            return {
                "ok": True,
                "written_files": self.written_files,
                "quality_passed": quality_result["success"],
            }

        except Exception as e:
            logger.error(f"NaturalTaskRunner failed: {e}")
            return {"ok": False, "error": str(e)}

    def _call_cloud_bridge(self, prompt: str) -> str:
        """Call cloud AI service using existing bridge"""
        from cloud_bridge import ask_cloud_ai

        enhanced_prompt = f"""
        {prompt}
        
        Please provide your response in one of these formats:
        
        Format 1 (preferred):
        <<<FILES
        filename1.py
        content of file 1
        <<<FILES
        filename2.py  
        content of file 2
        <<<FILES OK
        
        Format 2 (fallback):
        ```json
        {{
            "files": [
                {{"path": "filename1.py", "content": "content of file 1"}},
                {{"path": "filename2.py", "content": "content of file 2"}}
            ]
        }}
        ```
        """

        return ask_cloud_ai(enhanced_prompt)

    def _parse_files_response(self, response: str) -> List[Dict[str, str]]:
        """Parse files from cloud response, handling both formats robustly"""
        files = []

        if "<<<FILES" in response:
            files = self._parse_files_format(response)
            if files:
                return files

        if "```json" in response:
            files = self._parse_json_format(response)
            if files:
                return files

        logger.warning("No structured file format found in response")
        return []

    def _parse_files_format(self, response: str) -> List[Dict[str, str]]:
        """Parse <<<FILES format with robust handling of unterminated blocks"""
        files = []

        parts = re.split(r"<<<FILES\s*(?:OK)?", response)

        for i in range(1, len(parts)):
            part = parts[i].strip()
            if not part:
                continue

            lines = [line for line in part.split("\n") if line.strip()]
            if len(lines) < 2:
                continue

            filename = lines[0].strip()
            content = "\n".join(lines[1:])

            if filename and self._is_allowed_file(filename):
                files.append({"path": filename, "content": content})
                logger.info(f"Parsed file: {filename}")

        return files

    def _parse_json_format(self, response: str) -> List[Dict[str, str]]:
        """Parse JSON format from fenced code blocks"""
        try:
            json_match = re.search(r"```json\s*\n(.*?)\n```", response, re.DOTALL)
            if not json_match:
                return []

            data = json.loads(json_match.group(1))
            files = []

            for file_data in data.get("files", []):
                path = file_data.get("path", "")
                content = file_data.get("content", "")

                if path and self._is_allowed_file(path):
                    files.append({"path": path, "content": content})
                    logger.info(f"Parsed JSON file: {path}")

            return files

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON format: {e}")
            return []

    def _is_allowed_file(self, filepath: str) -> bool:
        """Check if file is in allowlist"""
        path_parts = Path(filepath).parts
        if not path_parts:
            return False

        first_part = path_parts[0]
        filename = Path(filepath).name

        return first_part in ALLOWED_FILES or filename in ALLOWED_FILES

    def _write_files(self, files_data: List[Dict[str, str]], output_dir: str):
        """Write files with logging and change detection"""
        for file_data in files_data:
            filepath = Path(file_data["path"])
            content = file_data["content"]

            filepath.parent.mkdir(parents=True, exist_ok=True)

            if filepath.exists():
                existing_content = filepath.read_text(encoding="utf-8")
                if existing_content == content:
                    logger.info(f"[writer] UNCHANGED {filepath}")
                    continue

            filepath.write_text(content, encoding="utf-8")
            self.written_files.append(str(filepath))
            logger.info(f"[writer] WROTE {filepath}")

    def _run_quality_gates(self) -> Dict[str, Any]:
        """Run quality gates: ruff, black --check, pytest"""
        from core.quality import run_quality_checks

        return run_quality_checks()

    def _run_critic_pass(self, errors: List[str]) -> Dict[str, Any]:
        """Run one critic pass to fix quality issues"""
        try:
            from cloud_bridge import ask_cloud_ai

            prompt = f"""
            The following quality check errors occurred:
            {chr(10).join(errors)}
            
            Please provide fixes for these issues in the same file format as before.
            Focus only on fixing the specific errors mentioned.
            """

            response = ask_cloud_ai(prompt)
            files_data = self._parse_files_response(response)

            if files_data:
                self._write_files(files_data, ".")
                return {"success": True}

            return {"success": False, "error": "No fixes provided"}

        except Exception as e:
            logger.error(f"Critic pass failed: {e}")
            return {"success": False, "error": str(e)}

    def _write_output_files(self, output_dir: str):
        """Write written_files.json, verify.txt, and update workspace/last_verify.txt"""
        output_path = Path(output_dir)

        written_files_path = output_path / "written_files.json"
        written_files_path.write_text(
            json.dumps(self.written_files, indent=2), encoding="utf-8"
        )

        verify_content = f"Job completed at {datetime.utcnow().isoformat()}Z\n"
        verify_content += f"Files written: {len(self.written_files)}\n"
        verify_content += "\n".join(self.written_files)

        verify_path = output_path / "verify.txt"
        verify_path.write_text(verify_content, encoding="utf-8")

        workspace_path = Path("workspace")
        workspace_path.mkdir(exist_ok=True)
        last_verify_path = workspace_path / "last_verify.txt"
        last_verify_path.write_text(verify_content, encoding="utf-8")
