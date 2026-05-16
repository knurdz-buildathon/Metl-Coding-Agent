import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Query

router = APIRouter(prefix="/tasks/{task_id}/workspace", tags=["workspace"])


async def _get_workspace_path(task_id: str, request: Request) -> Path:
    store = request.app.state.task_store
    task = await store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    from app.config import settings

    workspace_path = Path(settings.sandbox_base_dir) / task_id
    if not workspace_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace_path


@router.get("/tree")
async def get_file_tree(task_id: str, request: Request, path: str = Query("", alias="path")):
    """
    Return the file tree for the workspace, optionally scoped to a subdirectory.
    Response: { "tree": [{ "name": str, "path": str, "type": "file"|"directory", "children": [...] }] }
    """
    workspace = await _get_workspace_path(task_id, request)
    base = workspace / path if path else workspace

    if not base.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")

    ignore_patterns = {".git", "node_modules", "__pycache__", ".next", "dist", "build", ".DS_Store"}

    def build_tree(dir_path: Path, relative_to: Path) -> list[dict]:
        items = []
        try:
            entries = sorted(dir_path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return []

        for entry in entries:
            if entry.name in ignore_patterns or entry.name.startswith("."):
                continue

            rel_path = str(entry.relative_to(relative_to))

            if entry.is_dir():
                children = build_tree(entry, relative_to)
                if children:
                    items.append({
                        "name": entry.name,
                        "path": rel_path,
                        "type": "directory",
                        "children": children,
                    })
                else:
                    items.append({
                        "name": entry.name,
                        "path": rel_path,
                        "type": "directory",
                        "children": [],
                    })
            else:
                items.append({
                    "name": entry.name,
                    "path": rel_path,
                    "type": "file",
                })
        return items

    tree = build_tree(base, workspace)
    return {"tree": tree}


@router.get("/file")
async def read_file(task_id: str, request: Request, path: str = Query(...)):
    """Read a file from the workspace."""
    workspace = await _get_workspace_path(task_id, request)
    file_path = workspace / path

    resolved = file_path.resolve()
    if not str(resolved).startswith(str(workspace.resolve())):
        raise HTTPException(status_code=403, detail="Path traversal not allowed")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    if file_path.stat().st_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (>5MB)")

    content = file_path.read_text(encoding="utf-8", errors="replace")
    return {"path": path, "content": content, "size": file_path.stat().st_size}


@router.get("/diff")
async def get_diff(task_id: str, request: Request, path: str = Query(None)):
    """Get git diff for the workspace or a specific file."""
    workspace = await _get_workspace_path(task_id, request)
    import asyncio

    loop = asyncio.get_running_loop()

    if path:
        result = await loop.run_in_executor(
            None,
            lambda: os.popen(f"cd {workspace} && git diff HEAD -- {path} 2>/dev/null").read(),
        )
    else:
        result = await loop.run_in_executor(
            None,
            lambda: os.popen(f"cd {workspace} && git diff HEAD 2>/dev/null").read(),
        )

    return {"path": path, "diff": result}