from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState
from app.agents.nodes import (
    analyze_plan_node,
    clone_repo_node,
    execute_coding_step,
    inspect_preview_node,
    request_resources_node,
    apply_resources_node,
    generate_report_node,
)
from app.agents.nodes.browser_inspector import has_issues_decision


def should_continue(state: AgentState) -> Literal["continue", "inspect", "resources", "report"]:
    """Determine the next step in the agent loop."""
    task = state["task"]
    current_step = state["current_step"]
    total_steps = len(task.plan.steps)

    if current_step >= total_steps:
        return "report"

    if state["resources_requested"] and not state["resources_approved"]:
        return "resources"

    return "continue"


def build_agent_graph() -> StateGraph:
    """Build the LangGraph state machine for the coding agent."""

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("planner", analyze_plan_node)
    workflow.add_node("cloner", clone_repo_node)
    workflow.add_node("coder", execute_coding_step)
    workflow.add_node("inspector", inspect_preview_node)
    workflow.add_node("resource_requester", request_resources_node)
    workflow.add_node("resource_applier", apply_resources_node)
    workflow.add_node("reporter", generate_report_node)

    # Set the entry point
    workflow.set_entry_point("planner")

    # Add edges
    workflow.add_edge("planner", "cloner")
    workflow.add_edge("cloner", "coder")

    # Conditional: after each coding step, decide what to do next
    workflow.add_conditional_edges(
        "coder",
        should_continue,
        {
            "continue": "inspector",
            "resources": "resource_requester",
            "report": "reporter",
        },
    )

    # After inspection, decide if we need to fix issues
    workflow.add_conditional_edges(
        "inspector",
        has_issues_decision,
        {
            "fix": "coder",
            "continue": "coder",
        },
    )

    # Resource negotiation loop
    workflow.add_edge("resource_requester", "coder")  # Will send WS message, coder checks again
    
    # Report is final
    workflow.add_edge("reporter", END)

    # Compile with memory saver for state persistence
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


agent_graph = build_agent_graph()