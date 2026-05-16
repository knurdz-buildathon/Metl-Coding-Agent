import json
import uuid
from datetime import datetime
from typing import Optional

from app.config import settings
from app.models import Task, TaskStatus


class TaskStore:
    """In-memory task store with optional Redis persistence."""

    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._redis = None

    async def create(self, task_data: dict) -> Task:
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        from app.models import Plan

        plan_data = task_data.get("plan", {})
        if isinstance(plan_data, dict) and "original_prompt" not in plan_data:
            plan = Plan(original_prompt=task_data["prompt"])
        elif isinstance(plan_data, Plan):
            plan = plan_data
        else:
            plan = Plan(**plan_data)

        task = Task(
            id=task_id,
            status=TaskStatus.PENDING,
            github_url=task_data["github_url"],
            branch=task_data.get("branch", "main"),
            prompt=task_data["prompt"],
            plan=plan,
            available_resources=task_data.get("available_resources", []),
            callback_url=task_data.get("callback_url"),
            metadata=task_data.get("metadata", {}),
        )
        self._tasks[task_id] = task
        return task

    async def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    async def update(self, task_id: str, **kwargs) -> Optional[Task]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        task.updated_at = datetime.utcnow()
        return task

    async def add_log(self, task_id: str, entry: dict) -> None:
        task = self._tasks.get(task_id)
        if task:
            task.log.append(entry)
            task.updated_at = datetime.utcnow()

    async def add_error(self, task_id: str, error: str) -> None:
        task = self._tasks.get(task_id)
        if task:
            task.errors.append(error)
            task.updated_at = datetime.utcnow()

    async def list_tasks(self, limit: int = 50, offset: int = 0) -> list[Task]:
        tasks = sorted(
            self._tasks.values(),
            key=lambda t: t.created_at,
            reverse=True,
        )
        return tasks[offset : offset + limit]

    async def close(self):
        self._tasks.clear()