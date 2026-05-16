import json
import uuid
import aiosqlite
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import settings
from app.models import Task, TaskStatus, Plan, Resource, ResourceType


DB_PATH = Path(settings.sandbox_base_dir) / "metl_tasks.db"


class TaskStore:
    """SQLite-backed task store for persistence across restarts."""

    def __init__(self):
        self._db: Optional[aiosqlite.Connection] = None

    async def _init_db(self):
        if self._db is not None:
            return
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(str(DB_PATH))
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                github_url TEXT NOT NULL,
                branch TEXT NOT NULL DEFAULT 'main',
                prompt TEXT NOT NULL DEFAULT '',
                plan_original_prompt TEXT DEFAULT '',
                plan_original_plan_file TEXT,
                plan_enhanced_plan TEXT DEFAULT '',
                plan_steps TEXT DEFAULT '[]',
                available_resources TEXT DEFAULT '[]',
                callback_url TEXT,
                current_step INTEGER DEFAULT 0,
                total_steps INTEGER DEFAULT 0,
                workspace_path TEXT,
                preview_url TEXT,
                pr_url TEXT,
                errors TEXT DEFAULT '[]',
                report TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TEXT,
                updated_at TEXT
            )
        """)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                log_entry TEXT NOT NULL,
                created_at TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        await self._db.commit()

    async def create(self, task_data: dict) -> Task:
        await self._init_db()
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        resources_json = json.dumps([r.model_dump() if isinstance(r, Resource) else r for r in task.available_resources])
        plan_steps_json = json.dumps(task.plan.steps)

        await self._db.execute(
            """INSERT INTO tasks (id, status, github_url, branch, prompt,
               plan_original_prompt, plan_original_plan_file, plan_enhanced_plan,
               plan_steps, available_resources, callback_url,
               current_step, total_steps, workspace_path, preview_url, pr_url,
               errors, report, metadata, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task.id, task.status.value, task.github_url, task.branch, task.prompt,
                task.plan.original_prompt, task.plan.original_plan_file, task.plan.enhanced_plan,
                plan_steps_json, resources_json, task.callback_url,
                task.current_step, task.total_steps, None, None, None,
                "[]", None, "{}", now, now,
            ),
        )
        await self._db.commit()
        return task

    async def get(self, task_id: str) -> Optional[Task]:
        await self._init_db()
        cursor = await self._db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return self._row_to_task(row)

    async def update(self, task_id: str, **kwargs) -> Optional[Task]:
        await self._init_db()
        now = datetime.now(timezone.utc).isoformat()

        allowed_columns = {
            "status": str,
            "github_url": str,
            "branch": str,
            "prompt": str,
            "current_step": int,
            "total_steps": int,
            "workspace_path": str,
            "preview_url": str,
            "pr_url": str,
            "report": (dict, str),
            "metadata": dict,
        }

        updates = {}
        for key, value in kwargs.items():
            if key in allowed_columns:
                if key == "status" and isinstance(value, TaskStatus):
                    value = value.value
                elif key == "status" and isinstance(value, str):
                    pass
                elif key == "report" and isinstance(value, dict):
                    value = json.dumps(value)
                elif key == "metadata" and isinstance(value, dict):
                    value = json.dumps(value)
                updates[key] = value

        if not updates:
            task = await self.get(task_id)
            return task

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [now, task_id]
        await self._db.execute(
            f"UPDATE tasks SET {set_clause}, updated_at = ? WHERE id = ?",
            values,
        )
        await self._db.commit()

        return await self.get(task_id)

    async def add_log(self, task_id: str, entry: dict) -> None:
        await self._init_db()
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "INSERT INTO task_logs (task_id, log_entry, created_at) VALUES (?, ?, ?)",
            (task_id, json.dumps(entry), now),
        )
        await self._db.execute(
            "UPDATE tasks SET updated_at = ? WHERE id = ?", (now, task_id)
        )
        await self._db.commit()

    async def add_error(self, task_id: str, error: str) -> None:
        await self._init_db()
        task = await self.get(task_id)
        if task:
            errors = task.errors + [error]
            await self._db.execute(
                "UPDATE tasks SET errors = ?, updated_at = ? WHERE id = ?",
                (json.dumps(errors), datetime.now(timezone.utc).isoformat(), task_id),
            )
            await self._db.commit()

    async def list_tasks(self, limit: int = 50, offset: int = 0) -> list[Task]:
        await self._init_db()
        cursor = await self._db.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [self._row_to_task(row) for row in rows]

    async def get_logs(self, task_id: str) -> list[dict]:
        await self._init_db()
        cursor = await self._db.execute(
            "SELECT log_entry FROM task_logs WHERE task_id = ? ORDER BY id ASC",
            (task_id,),
        )
        rows = await cursor.fetchall()
        return [json.loads(row["log_entry"]) for row in rows]

    async def close(self):
        if self._db:
            await self._db.close()
            self._db = None

    def _row_to_task(self, row) -> Task:
        plan_steps = json.loads(row["plan_steps"]) if row["plan_steps"] else []
        resources_raw = json.loads(row["available_resources"]) if row["available_resources"] else []
        errors = json.loads(row["errors"]) if row["errors"] else []
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        report = json.loads(row["report"]) if row["report"] else None

        plan = Plan(
            original_prompt=row["plan_original_prompt"] or "",
            original_plan_file=row["plan_original_plan_file"],
            enhanced_plan=row["plan_enhanced_plan"] or "",
            steps=plan_steps,
        )

        resources = []
        for r in resources_raw:
            if isinstance(r, dict):
                rtype = r.get("type", "custom")
                try:
                    rtype = ResourceType(rtype)
                except ValueError:
                    rtype = ResourceType.CUSTOM
                resources.append(Resource(
                    type=rtype,
                    name=r.get("name", ""),
                    description=r.get("description"),
                    env_vars=r.get("env_vars", {}),
                    config=r.get("config", {}),
                ))

        return Task(
            id=row["id"],
            status=TaskStatus(row["status"]),
            github_url=row["github_url"],
            branch=row["branch"],
            prompt=row["prompt"],
            plan=plan,
            available_resources=resources,
            callback_url=row["callback_url"],
            current_step=row["current_step"],
            total_steps=row["total_steps"],
            errors=errors,
            report=report,
            metadata=metadata,
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(timezone.utc),
        )