"""
Optional v0 SDK integration for UI component generation.
Feature-flagged behind ENABLE_V0 env var.
"""

from app.config import settings


class V0Tool:
    """Wrapper around v0 SDK for UI component generation."""

    def __init__(self):
        self.enabled = settings.enable_v0
        self._client = None

    async def initialize(self):
        if not self.enabled:
            return
        try:
            import v0
            self._client = v0.Client(api_key=settings.v0_api_key)
        except ImportError:
            self.enabled = False

    async def generate_ui(self, prompt: str, project_context: str = "") -> dict:
        """
        Generate UI components from a natural language prompt.
        Returns generated code files and preview URLs.
        """
        if not self.enabled or not self._client:
            return {"success": False, "error": "v0 SDK not enabled", "files": []}

        try:
            result = await self._client.generate(
                prompt=prompt,
                context=project_context,
            )
            return {
                "success": True,
                "files": result.get("files", []),
                "preview_url": result.get("previewUrl"),
                "code": result.get("code", ""),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "files": []}

    async def generate_component(self, component_name: str, description: str) -> dict:
        """Generate a single UI component."""
        prompt = f"Create a React/Next.js component called {component_name}. {description}"
        return await self.generate_ui(prompt)