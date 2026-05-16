import os
import shutil
from pathlib import Path
from typing import Optional


class FsTool:
    """Filesystem operations for the agent."""

    def __init__(self, workspace_path: Path):
        self.workspace = workspace_path

    def read_file(self, path: str) -> Optional[str]:
        full_path = self.workspace / path
        if full_path.exists() and full_path.is_file():
            return full_path.read_text()
        return None

    def write_file(self, path: str, content: str) -> bool:
        full_path = self.workspace / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return True

    def list_files(self, pattern: str = "") -> list[str]:
        if pattern:
            return [str(p.relative_to(self.workspace)) for p in self.workspace.rglob(pattern)]
        return [str(p.relative_to(self.workspace)) for p in self.workspace.rglob("*") if p.is_file()]

    def file_exists(self, path: str) -> bool:
        return (self.workspace / path).exists()

    def delete_file(self, path: str) -> bool:
        full_path = self.workspace / path
        if full_path.exists():
            if full_path.is_file():
                full_path.unlink()
            else:
                shutil.rmtree(str(full_path))
            return True
        return False

    def get_file_size(self, path: str) -> int:
        full_path = self.workspace / path
        return full_path.stat().st_size if full_path.exists() else 0