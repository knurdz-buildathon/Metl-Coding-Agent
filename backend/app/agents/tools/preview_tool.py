import asyncio
import subprocess
from pathlib import Path
from typing import Optional


class PreviewTool:
    """Manage preview servers for frontend inspection."""

    def __init__(self, workspace_path: Path, port: int = 4000):
        self.workspace = workspace_path
        self.port = port
        self._process: Optional[asyncio.subprocess.Process] = None
        self._url: Optional[str] = None

    async def start(self, framework: str = "nextjs") -> str:
        """Start a dev server. Returns the URL."""
        self._url = f"http://localhost:{self.port}"

        if framework == "nextjs":
            # Check for next.config or similar to determine next 16 compatibilty
            pkg_path = self.workspace / "package.json"
            cmd = ["npx", "next", "dev", "--port", str(self.port)]
            if pkg_path.exists():
                import json
                pkg = json.loads(pkg_path.read_text())
                scripts = pkg.get("scripts", {})
                # Use existing dev script if available
                if "dev" in scripts:
                    cmd = ["npx", "next", "dev", "--port", str(self.port)]

        elif framework == "vite":
            cmd = ["npx", "vite", "--port", str(self.port), "--host"]
        else:
            cmd = ["npx", "next", "dev", "--port", str(self.port)]

        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.workspace),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Wait for server to be ready
        await asyncio.sleep(5)
        return self._url

    async def stop(self):
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=10)
            except asyncio.TimeoutError:
                self._process.kill()
            self._process = None

    @property
    def url(self) -> Optional[str]:
        return self._url

    async def health_check(self) -> bool:
        """Check if the dev server is responding."""
        import httpx

        if not self._url:
            return False
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self._url, timeout=5)
                return resp.status_code == 200
        except Exception:
            return False