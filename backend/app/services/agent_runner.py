import asyncio
import traceback
from datetime import datetime

from app.services.task_store import TaskStore
from app.services.event_bus import EventBus


class AgentRunner:
    def __init__(self, task_store: TaskStore, event_bus: EventBus):
        self.task_store = task_store
        self.event_bus = event_bus

    async def run_task(self, task_id: str):
        """Simple version for debugging."""
        try:
            task = await self.task_store.get(task_id)
            if not task:
                await self._log(task_id, "ERROR: Task not found")
                return

            await self.task_store.update(task_id, status="analyzing")
            await self._log(task_id, f"AGENT STARTED for task {task_id}")
            await self._log(task_id, f"Prompt: {task.prompt}")
            await self._log(task_id, "Note: Full LangGraph implementation coming in next iteration. For now, marking as completed for testing.")

            await self.task_store.update(task_id, status="completed", report={
                "task_id": task_id,
                "status": "completed",
                "summary": "Simple test task completed. Full agent implementation pending.",
                "github_branch": "metl/task-" + task_id,
                "steps_completed": 3,
            })
            await self._log(task_id, "Task marked as completed for testing.")

        except Exception as e:
            error = str(e)
            stack = traceback.format_exc()
            await self.task_store.add_error(task_id, f"{error}\n{stack}")
            await self.task_store.update(task_id, status="failed")
            await self._log(task_id, f"CRITICAL ERROR: {error}")
            await self._log(task_id, f"STACK: {stack[:300]}...")

    async def _log(self, task_id: str, message: str):
        log_entry = {"type": "log", "message": message, "timestamp": datetime.utcnow().isoformat()}
        await self.task_store.add_log(task_id, log_entry)
        try:
            await self.event_bus.publish(
                self.event_bus.task_channel(task_id),
                {"type": "log", "task_id": task_id, "message": message}
            )
        except Exception as e:
            print(f"Event bus error: {e}")


async def start_agent(task_id: str, task_store: TaskStore, event_bus: EventBus):
    """Start the agent."""
    runner = AgentRunner(task_store, event_bus)
    await runner.run_task(task_id)