import asyncio
import logging
import traceback
from datetime import datetime

from app.agents.graph import agent_graph
from app.agents.state import AgentState
from app.services.task_store import TaskStore
from app.services.event_bus import EventBus

logger = logging.getLogger("metl.agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class AgentRunner:
    def __init__(self, task_store: TaskStore, event_bus: EventBus):
        self.task_store = task_store
        self.event_bus = event_bus

    async def run_task(self, task_id: str):
        logger.info(f"=== AgentRunner.run_task() called for {task_id}")
        task = await self.task_store.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found in store")
            return

        await self.task_store.update(task_id, status="analyzing")
        await self._log(task_id, "Agent started. Analyzing prompt...")

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

            await self._log(task_id, "Starting LangGraph agent (planner -> cloner -> coder -> inspector -> reporter)")
            logger.info(f"LangGraph initial state ready. Entering astream()...")

            config = {"configurable": {"thread_id": task_id}}
            event_count = 0

            async for event in agent_graph.astream(initial_state, config):
                event_count += 1
                logger.info(f"Graph event {event_count}: keys={list(event.keys())}")

                if "task" in event:
                    updated = event["task"]
                    await self.task_store.update(
                        task_id,
                        status=updated.get("status", "coding"),
                        current_step=updated.get("current_step", 0),
                        total_steps=updated.get("total_steps", 0),
                        report=updated.get("report"),
                    )
                    logger.info(f"Task status updated: {updated.get('status')}")

                if "step_results" in event and event["step_results"]:
                    for r in event["step_results"]:
                        logger.info(f"Step result: {r.get('description', 'no description')[:100]}")
                        await self._log(task_id, f"Step {r.get('step_num','?')}: {r.get('description','')[:200]}")

                if "preview_url" in event and event.get("preview_url"):
                    await self.task_store.update(task_id, preview_url=event["preview_url"])
                    logger.info(f"Preview URL: {event['preview_url']}")
                    await self._log(task_id, f"Preview available at: {event['preview_url']}")

                if "report" in event and event.get("report"):
                    await self.task_store.update(task_id, report=event["report"])
                    logger.info("Report received. Agent completed.")
                    await self._log(task_id, "Task completed. PR created.")
                    break

            logger.info(f"LangGraph finished after {event_count} events")
            await self.task_store.update(task_id, status="completed")
            await self._log(task_id, "Agent finished successfully.")

        except Exception as exc:
            error_msg = str(exc)
            stack = traceback.format_exc()
            logger.error(f"Agent failed: {error_msg}")
            logger.error(stack[:800])
            await self.task_store.add_error(task_id, f"{error_msg}\n{stack}")
            await self.task_store.update(task_id, status="failed")
            await self._log(task_id, f"CRITICAL ERROR: {error_msg}")

    async def _log(self, task_id: str, message: str):
        logger.info(message)
        entry = {"type": "log", "message": message, "timestamp": datetime.utcnow().isoformat()}
        await self.task_store.add_log(task_id, entry)
        try:
            await self.event_bus.publish(
                self.event_bus.task_channel(task_id),
                {"type": "log", "task_id": task_id, "message": message},
            )
        except Exception as exc:
            logger.warning(f"Event bus publish failed: {exc}")


async def start_agent(task_id: str, task_store: TaskStore, event_bus: EventBus):
    """Start the autonomous coding agent."""
    logger.info(f"start_agent() called for task {task_id}")
    runner = AgentRunner(task_store, event_bus)
    await runner.run_task(task_id)