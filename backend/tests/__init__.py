import pytest
from app.models import TaskCreate, Task, TaskStatus
from app.services.task_store import TaskStore


@pytest.mark.asyncio
async def test_create_task():
    store = TaskStore()
    task_data = {
        "github_url": "https://github.com/org/repo",
        "branch": "main",
        "prompt": "Build a todo app",
    }
    task = await store.create(task_data)
    assert task.id.startswith("task_")
    assert task.status == TaskStatus.PENDING
    assert task.prompt == "Build a todo app"


@pytest.mark.asyncio
async def test_get_task():
    store = TaskStore()
    task_data = {
        "github_url": "https://github.com/org/repo",
        "prompt": "Build a todo app",
    }
    task = await store.create(task_data)
    fetched = await store.get(task.id)
    assert fetched is not None
    assert fetched.id == task.id


@pytest.mark.asyncio
async def test_update_task():
    store = TaskStore()
    task = await store.create({
        "github_url": "https://github.com/org/repo",
        "prompt": "Build a todo app",
    })
    await store.update(task.id, status="coding")
    updated = await store.get(task.id)
    assert updated is not None
    assert updated.status == TaskStatus.CODING


@pytest.mark.asyncio
async def test_add_log():
    store = TaskStore()
    task = await store.create({
        "github_url": "https://github.com/org/repo",
        "prompt": "Build a todo app",
    })
    await store.add_log(task.id, {"type": "log", "message": "Working..."})
    updated = await store.get(task.id)
    assert len(updated.log) == 1
    assert updated.log[0]["message"] == "Working..."