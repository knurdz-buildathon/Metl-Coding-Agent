from typing import TypedDict, Optional, Any, Union
from pathlib import Path
from app.models import Task, TaskStatus, Plan, Resource


def get_task(state: AgentState) -> Task:
    """Return a Task model instance from state, rehydrating if langgraph replaced it with a dict."""
    task = state["task"]
    if isinstance(task, Task):
        return task
    return Task(**task)


class AgentState(TypedDict):
    """LangGraph state for the coding agent."""
    task: Union[Task, dict[str, Any]]
    workspace_path: Optional[str]
    current_step: int
    step_results: list[dict[str, Any]]
    errors: list[str]
    resources_requested: list[Resource]
    resources_approved: list[Resource]
    pr_url: Optional[str]
    preview_url: Optional[str]
    report: Optional[dict[str, Any]]