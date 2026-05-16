import asyncio
import json
from datetime import datetime
from typing import Any

from app.agents.graph import agent_graph
from app.agents.state import AgentState
from app.models import Task, Plan, Resource
from app.services.task_store import TaskStore
from app.services.event_bus import EventBus


class AgentRunner:
    """Runs the LangGraph agent for a task and updates the task store."""

    def __init__(self, task_store: TaskStore, event_bus: EventBus):
        self.task_store = task_store
        self.event_bus = event_bus

    async def run_task(self, task_id: str):
        """Run the agent for a given task."""
        task = await self.task_store.get(task_id)
        if not task:
            return

        await self.task_store.update(task_id, status="analyzing")
        await self._publish_status(task_id, "analyzing", 10)

        try:
            # Initial state
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
            await self._publish_status(task_id, "planning", 20)

            # Run the LangGraph
            config = {"configurable": {"thread_id": task_id}}
            async for event in agent_graph.astream(initial_state, config):
                if "task" in event:
                    updated_task = event["task"]
                    await self.task_store.update(
                        task_id,
                        status=updated_task.get("status", "coding"),
                        current_step=updated_task.get("current_step", 0),
                        total_steps=updated_task.get("total_steps", 0),
                        report=updated_task.get("report"),
                    )

                if "step_results" in event:
                    await self.task_store.add_log(
                        task_id,
                        {"type": "step", "data": event["step_results"][-1]},
                    )

                if "preview_url" in event and event["preview_url"]:
                    await self.task_store.update(task_id, preview_url=event["preview_url"])
                    await self._publish_event(
                        task_id, "preview_ready", {"url": event["preview_url"]}
                    )

                if "report" in event and event["report"]:
                    await self.task_store.update(task_id, report=event["report"])
                    await self._publish_event(task_id, "completed", {"report": event["report"]})
                    break

            await self.task_store.update(task_id, status="completed")
            await self._publish_status(task_id, "completed", 100)

        except Exception as e:
            error_msg = str(e)
            await self.task_store.add_error(task_id, error_msg)
            await self.task_store.update(task_id, status="failed")
            await self._publish_event(task_id, "error", {"message": error_msg})

    async def _publish_status(self, task_id: str, step: str, progress: int):
        await self.event_bus.publish(
            self.event_bus.task_channel(task_id),
            {"type": "status", "task_id": task_id, "step": step, "progress": progress},
        )

    async def _publish_event(self, task_id: str, event_type: str, payload: dict):
        await self.event_bus.publish(
            self.event_bus.task_channel(task_id),
            {"type": event_type, "task_id": task_id, "payload": payload},
        )


async def start_agent(task_id: str, task_store: TaskStore, event_bus: EventBus):
    """Background task to run the agent."""
    runner = AgentRunner(task_store, event_bus)
    await runner.run_task(task_id)