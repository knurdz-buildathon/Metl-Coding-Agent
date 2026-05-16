import asyncio
import os
import subprocess
from pathlib import Path
from typing import Optional

from app.config import settings


class AiderTool:
    """Wrapper around Aider CLI for autonomous code generation."""

    def __init__(self, workspace_path: Path, llm_provider: str = "", llm_model: str = ""):
        self.workspace_path = workspace_path
        self.llm_provider = llm_provider or settings.aider_llm_provider
        self.llm_model = llm_model or settings.aider_llm_model
        self._process: Optional[asyncio.subprocess.Process] = None

    def _build_env(self) -> dict[str, str]:
        """Build environment variables for the Aider subprocess, including Azure Foundry overrides."""
        env = os.environ.copy()
        if settings.openai_api_base:
            env["OPENAI_API_BASE"] = settings.openai_api_base
        if settings.openai_api_version:
            env["OPENAI_API_VERSION"] = settings.openai_api_version
        if settings.openai_org_id:
            env["OPENAI_ORG_ID"] = settings.openai_org_id
        return env

    async def run(self, prompt: str, file_patterns: list[str] | None = None) -> dict:
        """
        Execute Aider with a prompt on the workspace.
        
        Returns dict with:
          - success: bool
          - output: str (raw aider output)
          - files_changed: list[str]
          - error: str | None
        """
        cmd = [
            "aider",
            "--model", f"{self.llm_provider}/{self.llm_model}",
            "--yes-always",           # Non-interactive
            "--no-auto-commits",      # We control commits
            "--no-dirty-commits",
            "--no-suggest-shell-commands",
            "--no-show-model-warnings",
            "--no-suggest-shell-commands",
            "--message", prompt,
            "--no-git",               # We manage git ourselves
            "--cache-prompts",
            "--lint", "no",
        ]

        if file_patterns:
            cmd.extend(file_patterns)
        else:
            cmd.append(str(self.workspace_path))

        import json, time, traceback  # #region agent log
        _dl_path = "/tmp/metl-debug-a493e7.log"
        def _dl(msg, data, hid="H3"):
            _dl_obj = json.dumps({"sessionId":"a493e7","id":"log_"+str(int(time.time()*1000)),"timestamp":int(time.time()*1000),"location":"aider_tool.py:62","message":msg,"data":data,"runId":"debug","hypothesisId":hid})
            print("[METL_DEBUG] " + _dl_obj)
            try:
                with open(_dl_path,"a") as f: f.write(_dl_obj+"\n")
            except Exception: pass
        _dl("H3: aider run start", {"cmd":" ".join(cmd[:8]),"cwd":str(self.workspace_path),"exists":self.workspace_path.exists()}, "H3")
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace_path),
                capture_output=True,
                text=True,
                timeout=600,  # 10 min timeout per Aider call
                env=self._build_env(),
            )

            output = result.stdout + result.stderr
            success = result.returncode == 0
            _dl("H3: aider subprocess finished", {"returncode":result.returncode,"output_len":len(output)}, "H3")

            # Parse changed files from aider output
            files_changed = self._parse_changed_files(output)

            return {
                "success": success,
                "output": output,
                "files_changed": files_changed,
                "error": result.stderr if not success else None,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "files_changed": [],
                "error": "Aider timed out after 600 seconds",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "output": "",
                "files_changed": [],
                "error": "Aider not found. Install with: pip install aider-chat",
            }

    def _parse_changed_files(self, output: str) -> list[str]:
        """Extract list of changed files from aider output."""
        files = []
        for line in output.split("\n"):
            if "Creating" in line or "Updating" in line or "Added" in line:
                # Format: "Creating /path/to/file.py" or "Updating file.py"
                for keyword in ["Creating ", "Updating ", "Added "]:
                    if keyword in line:
                        fname = line.split(keyword)[-1].strip()
                        if fname:
                            files.append(fname)
        return files