from pydantic import BaseModel
from typing import Optional


class Report(BaseModel):
    task_id: str
    status: str
    github_pr_url: Optional[str] = None
    github_branch: Optional[str] = None
    git_diff_summary: str = ""
    files_created: list[str] = []
    files_modified: list[str] = []
    resources_used: list[str] = []
    env_vars_required: dict[str, str] = {}
    preview_url: Optional[str] = None
    issues_found_and_fixed: int = 0
    steps_completed: int = 0
    duration_seconds: float = 0.0
    summary: str = ""