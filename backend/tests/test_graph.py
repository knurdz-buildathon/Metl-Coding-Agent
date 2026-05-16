import pytest
from app.agents.state import AgentState
from app.models import Task, Plan, TaskStatus


def test_agent_state_structure():
    """Verify the AgentState TypedDict has all required fields."""
    state: AgentState = {
        "task": Task(
            id="test_id",
            github_url="https://github.com/org/repo",
            prompt="Test prompt",
            plan=Plan(
                original_prompt="Test prompt",
                steps=["Step 1", "Step 2"],
            ),
        ),
        "workspace_path": "/tmp/test",
        "current_step": 0,
        "step_results": [],
        "errors": [],
        "resources_requested": [],
        "resources_approved": [],
        "pr_url": None,
        "preview_url": None,
        "report": None,
    }
    assert state["task"].id == "test_id"
    assert len(state["task"].plan.steps) == 2
    assert state["current_step"] == 0