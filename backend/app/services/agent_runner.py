import asyncio
import traceback
from datetime import datetime

from app.agents.graph import agent_graph
from app.agents.state import AgentState
from app.services.task_store import TaskStore
from app.services.event_bus import EventBus


class AgentRunner:
    def __init__(self, task_store: TaskStore, event_bus: EventBus):
        self.task_store = task_store
        self.event_bus = event_bus

    async def run_task(self, task_id: str):
        """Run the autonomous coding agent with extensive logging."""
        task = await self.task_store.get(task_id)
        if not task:
            await self._log(task_id, "ERROR: Task not found")
            return

        await self.task_store.update(task_id, status="analyzing")
        await self._log(task_id, f"Agent started for task {task_id}. Prompt: {task.prompt[:80]}...")

        try:
            initial_state: AgentState = {
                "task": task,
                "workspace_path": None,
                "current_step": 0,
                "step_results": [],
                "errors": [],
                "resources_requested": [],
                "resources_approved": task.available_resources or [],
                "pr_url": None,
                "preview_url": None,
                "report": None,
            }

            await self.task_store.update(task_id, status="planning")
            await self._log(task_id, "Step 1: Creating enhanced implementation plan...")

            config = {"configurable": {"thread_id": task_id}}
            event_count = 0

            async for event in agent_graph.astream(initial_state, config):
                event_count += 1
                await self._log(task_id, f"Graph event {event_count}: {list(event.keys())}")

                if "task" in event:
                    updated = event["task"]
                    await self.task_store.update(
                        task_id,
                        status=updated.get("status", "coding"),
                        current_step=updated.get("current_step", 0),
                        total_steps=updated.get("total_steps", 0),
                        report=updated.get("report"),
                    )
                    await self._log(task_id, f"Task status updated to: {updated.get('status')}")

                if "step_results" in event and event["step_results"]:
                    for result in event["step_results"]:
                        await self._log(task_id, f"STEP RESULT: {result.get('description', '')}")

                if "preview_url" in event and event.get("preview_url"):
                    await self.task_store.update(task_id, preview_url=event["preview_url"])
                    await self._log(task_id, f"PREVIEW READY: {event['preview_url']}")

                if "report" in event and event.get("report"):
                    await self.task_store.update(task_id, report=event["report"])
                    await self._log(task_id, "Task completed successfully. PR created.")
                    break

            await self.task_store.update(task_id, status="completed")
            await self._log(task_id, f"Agent finished. Processed {event_count} graph events.")

        except Exception as e:
            error_msg = str(e)
            stack = traceback.format_exc()
            await self.task_store.add_error(task_id, f"{error_msg}\n{stack}")
            await self.task_store.update(task_id, status="failed")
            await self._log(task_id, f"AGENT FAILED: {error_msg}")
            await self._log(task_id, f"Stack trace: {stack[:500]}...")

    async def _log(self, task_id: str, message: str):
        log_entry = {"type": "log", "message": message, "timestamp": datetime.utcnow().isoformat()}
        await self.task_store.add_log(task_id, log_entry)
        try:
            await self.event_bus.publish(
                self.event_bus.task_channel(task_id),
                {"type": "log", "task_id": task_id, "message": message}
            )
        except:
            pass  # Event bus may not be available


async def start_agent(task_id: str, task_store: TaskStore, event_bus: EventBus):
    """Start the agent for a task with full error handling."""
    runner = AgentRunner(task_store, event_bus)
    await runner.run_task(task_id)