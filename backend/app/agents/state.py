from typing import TypedDict, Optional, Any
from pathlib import Path
from app.models import Task, TaskStatus, Plan, Resource


class AgentState(TypedDict):
    """LangGraph state for the coding agent."""
    task: Task
    workspace_path: Optional[str]
    current_step: int
    step_results: list[dict[str, Any]]
    errors: list[str]
    resources_requested: list[Resource]
    resources_approved: list[Resource]
    pr_url: Optional[str]
    preview_url: Optional[str]
    report: Optional[dict[str, Any]]