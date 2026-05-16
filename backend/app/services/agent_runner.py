import asyncio
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
        """Run the autonomous coding agent."""
        task = await self.task_store.get(task_id)
        if not task:
            return

        await self.task_store.update(task_id, status="analyzing")
        await self._log(task_id, "Agent started. Analyzing requirements...")

        try:
            initial_state = {
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
            await self._log(task_id, "Creating implementation plan...")

            config = {"configurable": {"thread_id": task_id}}
            async for event in agent_graph.astream(initial_state, config):
                if "task" in event:
                    updated = event["task"]
                    await self.task_store.update(
                        task_id,
                        status=updated.get("status", "coding"),
                        current_step=updated.get("current_step", 0),
                        total_steps=updated.get("total_steps", 0),
                        report=updated.get("report"),
                    )

                if "step_results" in event:
                    for result in event["step_results"]:
                        await self._log(task_id, f"Step {result.get('step_num', 0)}: {result.get('description', '')}")

                if "preview_url" in event and event.get("preview_url"):
                    await self.task_store.update(task_id, preview_url=event["preview_url"])
                    await self._log(task_id, f"Preview available at: {event['preview_url']}")

                if "report" in event and event.get("report"):
                    await self.task_store.update(task_id, report=event["report"])
                    await self._log(task_id, "Task completed. PR created.")
                    break

            await self.task_store.update(task_id, status="completed")
            await self._log(task_id, "Agent finished successfully.")

        except Exception as e:
            error = str(e)
            await self.task_store.add_error(task_id, error)
            await self.task_store.update(task_id, status="failed")
            await self._log(task_id, f"Agent failed: {error}")

    async def _log(self, task_id: str, message: str):
        await self.task_store.add_log(task_id, {"type": "log", "message": message})
        await self.event_bus.publish(
            self.event_bus.task_channel(task_id),
            {"type": "log", "task_id": task_id, "message": message}
        )


async def start_agent(task_id: str, task_store: TaskStore, event_bus: EventBus):
    """Start the agent for a task."""
    runner = AgentRunner(task_store, event_bus)
    await runner.run_task(task_id)