import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from git import Repo, GitCommandError

from app.config import settings


class Workspace:
    """Manages a git-based workspace for a single task."""

    def __init__(self, task_id: str, github_url: str, branch: str = "main"):
        self.task_id = task_id
        self.github_url = github_url
        self.branch = branch
        self.branch_name = f"metl/task-{task_id}"
        self.work_dir: Path = Path(settings.sandbox_base_dir) / task_id
        self.repo: Repo | None = None

    async def clone(self) -> Path:
        """Clone the repo and create a feature branch."""
        self.work_dir.mkdir(parents=True, exist_ok=True)
        print(f"[Workspace] cloning {self.github_url} into {self.work_dir}")

        auth_url = self._authenticated_url()
        if not auth_url:
            raise ValueError("github_url is empty — task state was corrupted")

        loop = asyncio.get_running_loop()
        self.repo = await loop.run_in_executor(None, Repo.clone_from, auth_url, str(self.work_dir))

        # Create feature branch from target branch
        if self.branch != "main":
            await loop.run_in_executor(None, self.repo.git.checkout, self.branch)

        await loop.run_in_executor(None, self.repo.git.checkout, "-b", self.branch_name)
        return self.work_dir

    async def commit(self, message: str) -> str:
        """Stage all changes and commit. Returns commit hash."""
        if not self.repo:
            raise RuntimeError("Workspace not cloned. Call clone() first.")

        self.repo.git.add("--all")
        if self.repo.is_dirty(untracked_files=True):
            commit = self.repo.index.commit(message)
            return commit.hexsha
        return ""

    async def push(self) -> str:
        """Push the current branch to origin. Returns branch name."""
        if not self.repo:
            raise RuntimeError("Workspace not cloned.")
        self.repo.git.push("--set-upstream", "origin", self.branch_name)
        return self.branch_name

    async def create_pr(self, title: str, body: str) -> str:
        """Create a PR via GitHub API. Returns PR URL."""
        import httpx

        owner, repo_name = self._parse_github_url()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/repos/{owner}/{repo_name}/pulls",
                headers={
                    "Authorization": f"Bearer {settings.github_pat}",
                    "Accept": "application/vnd.github+json",
                },
                json={
                    "title": title,
                    "head": self.branch_name,
                    "base": self.branch,
                    "body": body,
                    "labels": ["metl-generated"],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["html_url"]

    async def get_diff_summary(self) -> str:
        """Get a summary of changes since the base branch."""
        if not self.repo:
            return ""
        diff = self.repo.git.diff(f"origin/{self.branch}...HEAD", stat=True)
        return diff

    async def cleanup(self):
        """Remove the workspace directory."""
        if self.work_dir.exists():
            shutil.rmtree(str(self.work_dir), ignore_errors=True)

    def _authenticated_url(self) -> str:
        """Convert HTTPS URL to authenticated URL using PAT."""
        pat = settings.github_pat
        if not pat:
            raise ValueError("GITHUB_PAT is required for authenticated clone")
        if "github.com" not in self.github_url:
            return self.github_url

        # Format: https://<PAT>@github.com/owner/repo.git
        # Fine-grained PAT works with plain token@host
        url = self.github_url.rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]
        return f"https://{pat}@{url.split('://', 1)[1]}.git"

    def _parse_github_url(self) -> tuple[str, str]:
        """Extract owner and repo name from GitHub URL."""
        url = self.github_url.rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]
        parts = url.split("/")
        return parts[-2], parts[-1]