from app.agents.state import AgentState, get_task, task_update
from app.models import Resource, TaskStatus
from app.services.resource_catalog import ResourceCatalog


async def request_resources_node(state: AgentState) -> dict:
    """Identify and request resources the project needs from control panel."""
    task = get_task(state)
    catalog = ResourceCatalog()
    
    resources_needed = []
    
    # Check what resources the plan identified
    for step in task.plan.steps:
        step_lower = step.lower()
        for name, entry in catalog._entries.items():
            if entry.resource_type in step_lower or name in step_lower:
                if entry.resource_type not in [r.type for r in resources_needed]:
                    resources_needed.append({
                        "type": entry.resource_type,
                        "name": entry.name,
                        "description": entry.description,
                        "env_vars": entry.env_vars,
                        "reason": f"Required for: {step[:100]}",
                    })

    return {
        "resources_requested": resources_needed,
        "task": task_update(state, status=TaskStatus.WAITING_FOR_RESOURCE),
    }


async def apply_resources_node(state: AgentState) -> dict:
    """Apply approved resources to the project configuration."""
    import os
    from pathlib import Path

    workspace = Path(state["workspace_path"])
    
    # Update .env.example with approved resource env vars
    env_example_path = workspace / ".env.example"
    existing_content = ""
    if env_example_path.exists():
        existing_content = env_example_path.read_text()

    new_vars = []
    for resource in state["resources_approved"]:
        for var_name, var_value in resource.env_vars.items():
            var_line = f"{var_name}={var_value}"
            if var_name not in existing_content:
                new_vars.append(var_line)

    if new_vars:
        with open(env_example_path, "a") as f:
            f.write("\n# Resources provided by control panel\n")
            for var in new_vars:
                f.write(f"{var}\n")

    return {
        "task": task_update(state, status=TaskStatus.CODING),
    }