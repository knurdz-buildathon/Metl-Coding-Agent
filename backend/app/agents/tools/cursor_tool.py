"""
Optional Cursor SDK integration.
Feature-flagged behind ENABLE_CURSOR_SDK env var.
Can be completely removed if the dependency becomes a liability.
"""

from app.config import settings


class CursorTool:
    """
    Wrapper around @cursor/sdk for complex coding tasks.
    Used as a supplement when Aider struggles with:
    - Complex multi-file refactoring
    - Understanding large codebase architecture
    - Tasks requiring deep AST-level transformations
    """

    def __init__(self):
        self.enabled = settings.enable_cursor_sdk
        self._api_key = settings.cursor_api_key
        self._client = None

    async def initialize(self):
        if not self.enabled:
            return
        try:
            from cursor import Agent
            self._client = Agent
        except ImportError:
            self.enabled = False

    async def run_task(self, prompt: str, workspace_path: str) -> dict:
        """
        Execute a coding task using Cursor agent.
        Returns the result of the agent's work.
        """
        if not self.enabled or not self._client:
            return {"success": False, "error": "Cursor SDK not enabled", "output": ""}

        try:
            agent = await self._client.create(
                apiKey=self._api_key,
                local={"cwd": workspace_path},
            )
            
            run = await agent.send(prompt)
            output = ""
            async for event in run.stream():
                output += str(event)

            return {
                "success": True,
                "output": output,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "output": ""}

    async def refactor(self, description: str, files: list[str], workspace_path: str) -> dict:
        """Refactor specified files based on a description."""
        prompt = f"""Refactor the following files according to this description:
{description}

Files to modify:
{chr(10).join(f'- {f}' for f in files)}

Apply the refactoring carefully, maintaining code quality and consistency."""
        return await self.run_task(prompt, workspace_path)