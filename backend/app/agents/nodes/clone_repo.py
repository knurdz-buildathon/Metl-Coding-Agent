import os
from pathlib import Path

from app.agents.state import AgentState, get_task, task_update, task_update
from app.models import TaskStatus
from app.sandbox.workspace import Workspace


async def clone_repo_node(state: AgentState) -> dict:
    """Clone the repository and set up the feature branch."""
    task = get_task(state)
    workspace = Workspace(
        task_id=task.id,
        github_url=task.github_url,
        branch=task.branch,
    )

    work_dir = await workspace.clone()
    return {
        "workspace_path": str(work_dir),
        "task": task_update(state, status=TaskStatus.CLONING),
    }