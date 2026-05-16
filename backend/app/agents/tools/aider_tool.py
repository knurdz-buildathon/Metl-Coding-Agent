import asyncio
import os
import subprocess
from pathlib import Path
from typing import Optional, AsyncGenerator

from app.config import settings


class AiderTool:
    """Wrapper around Aider CLI for autonomous code generation with real-time streaming."""

    def __init__(self, workspace_path: Path, llm_provider: str = "", llm_model: str = ""):
        self.workspace_path = workspace_path
        self.llm_provider = llm_provider or settings.aider_llm_provider
        self.llm_model = llm_model or settings.aider_llm_model
        self._process: Optional[asyncio.subprocess.Process] = None

    def _build_env(self) -> dict[str, str]:
        env = os.environ.copy()
        if settings.openai_api_base:
            env["OPENAI_API_BASE"] = settings.openai_api_base
        if settings.openai_api_version:
            env["OPENAI_API_VERSION"] = settings.openai_api_version
        if settings.openai_org_id:
            env["OPENAI_ORG_ID"] = settings.openai_org_id
        return env

    def _build_cmd(self, prompt: str, file_patterns: list[str] | None = None) -> list[str]:
        cmd = [
            "aider",
            "--model", f"{self.llm_provider}/{self.llm_model}",
            "--yes-always",
            "--no-auto-commits",
            "--no-dirty-commits",
            "--no-suggest-shell-commands",
            "--no-show-model-warnings",
            "--message", prompt,
            "--no-git",
            "--cache-prompts",
            "--lint", "no",
        ]
        if file_patterns:
            cmd.extend(file_patterns)
        else:
            cmd.append(str(self.workspace_path))
        return cmd

    async def _parse_changed_files(self, output: str) -> list[str]:
        files = []
        for line in output.split("\n"):
            for keyword in ["Creating ", "Updating ", "Added "]:
                if keyword in line:
                    fname = line.split(keyword)[-1].strip()
                    if fname:
                        files.append(fname)
        return files

    async def stream(
        self,
        prompt: str,
        file_patterns: list[str] | None = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Execute Aider and yield streaming output events.

        Yields dicts with:
          - type: "aider_output" for stdout/stderr lines
          - type: "aider_done" when finished (with success, output, files_changed, error)
        """
        cmd = self._build_cmd(prompt, file_patterns)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.workspace_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=self._build_env(),
            )

            output_lines = []

            async for line in process.stdout:
                line_str = line.decode("utf-8", errors="replace").rstrip("\n")
                output_lines.append(line_str)
                yield {"type": "aider_output", "line": line_str}

            await process.wait()

            output = "\n".join(output_lines)
            success = process.returncode == 0
            files_changed = await self._parse_changed_files(output)

            yield {
                "type": "aider_done",
                "success": success,
                "output": output,
                "files_changed": files_changed,
                "error": output[-2000:] if not success else None,
            }

        except FileNotFoundError:
            yield {
                "type": "aider_done",
                "success": False,
                "output": "",
                "files_changed": [],
                "error": "Aider not found. Install with: pip install aider-chat",
            }

    async def run(self, prompt: str, file_patterns: list[str] | None = None) -> dict:
        """
        Execute Aider (non-streaming for backward compat).
        Returns dict with success, output, files_changed, error.
        """
        result = None
        async for event in self.stream(prompt, file_patterns):
            if event["type"] == "aider_done":
                result = event

        if result is None:
            return {
                "success": False,
                "output": "",
                "files_changed": [],
                "error": "Aider process produced no result",
            }
        return result