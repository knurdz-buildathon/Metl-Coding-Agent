from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from app.models import TaskCreate
from app.services.task_store import TaskStore
from app.services.agent_runner import start_agent

router = APIRouter(prefix="/tasks", tags=["tasks"])


class ContinueTaskRequest(BaseModel):
    prompt: str


@router.post("")
async def create_task(
    task_data: TaskCreate,
    request: Request,
    background_tasks: BackgroundTasks,
):
    store: TaskStore = request.app.state.task_store
    event_bus = request.app.state.event_bus

    task = await store.create(task_data.model_dump())
    background_tasks.add_task(start_agent, task.id, store, event_bus)
    return {"task_id": task.id, "status": task.status.value}


@router.get("")
async def list_tasks(request: Request, limit: int = 50, offset: int = 0):
    store: TaskStore = request.app.state.task_store
    tasks = await store.list_tasks(limit=limit, offset=offset)
    return {
        "tasks": [
            {
                "id": t.id,
                "status": t.status.value,
                "github_url": t.github_url,
                "prompt": t.prompt[:100],
                "current_step": t.current_step,
                "total_steps": t.total_steps,
                "created_at": t.created_at.isoformat(),
            }
            for t in tasks
        ]
    }


@router.get("/{task_id}")
async def get_task(task_id: str, request: Request):
    store: TaskStore = request.app.state.task_store
    task = await store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task.id,
        "status": task.status.value,
        "github_url": task.github_url,
        "branch": task.branch,
        "prompt": task.prompt,
        "current_step": task.current_step,
        "total_steps": task.total_steps,
        "errors": task.errors,
        "workspace_path": f"/api/v1/tasks/{task_id}/workspace/tree",
        "preview_url": task.preview_url,
        "pr_url": task.pr_url,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "report": task.report,
        "plan": {
            "steps": task.plan.steps,
            "enhanced_plan": task.plan.enhanced_plan,
        },
    }


@router.post("/{task_id}/continue")
async def continue_task(
    task_id: str,
    continue_req: ContinueTaskRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Send a follow-up prompt to continue working on a completed task.
    The agent will be restarted on the existing workspace with the new prompt.
    """
    store: TaskStore = request.app.state.task_store
    event_bus = request.app.state.event_bus

    task = await store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    combined_prompt = f"{task.prompt}\n\n--- Additional Instructions ---\n{continue_req.prompt}"
    await store.update(task_id, prompt=combined_prompt, status="pending", current_step=0)

    background_tasks.add_task(start_agent, task_id, store, event_bus)
    return {"task_id": task_id, "status": "pending", "message": "Agent restarted with follow-up prompt"}


@router.delete("/{task_id}")
async def cancel_task(task_id: str, request: Request):
    store: TaskStore = request.app.state.task_store
    task = await store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await store.update(task_id, status="cancelled")
    return {"status": "cancelled"}


@router.get("/{task_id}/report")
async def get_task_report(task_id: str, request: Request):
    store: TaskStore = request.app.state.task_store
    task = await store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not task.report:
        raise HTTPException(status_code=404, detail="Report not yet generated")
    return task.report


@router.get("/{task_id}/logs")
async def get_task_logs(task_id: str, request: Request):
    store: TaskStore = request.app.state.task_store
    task = await store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    logs = await store.get_logs(task_id)
    return {"logs": logs}