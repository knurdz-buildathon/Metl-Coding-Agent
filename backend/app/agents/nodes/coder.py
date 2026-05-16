import json
from pathlib import Path

from app.agents.state import AgentState
from app.models import TaskStatus
from app.agents.tools.aider_tool import AiderTool
from app.agents.tools.fs_tool import FsTool
from app.agents.prompts import CODER_SYSTEM_PROMPT


async def execute_coding_step(state: AgentState) -> dict:
    """Execute the current step in the plan using Aider."""
    task = state["task"]
    workspace = Path(state["workspace_path"])
    aidertool = AiderTool(workspace)
    fstool = FsTool(workspace)

    current_step = state["current_step"]
    steps = task.plan.steps

    if current_step >= len(steps):
        return {"errors": ["No more steps to execute"]}

    step_description = steps[current_step]
    
    # Read existing project files for context
    pkg_json = fstool.read_file("package.json")
    readme = fstool.read_file("README.md")
    existing_files = fstool.list_files()

    context = f"""
Project files:
{chr(10).join(existing_files[:30])}

package.json:
{pkg_json[:2000] if pkg_json else 'N/A'}

README.md:
{readme[:1000] if readme else 'N/A'}
"""

    prompt = f"""{CODER_SYSTEM_PROMPT}

Current Workspace Context:
{context}

Implementation Step {current_step + 1}/{len(steps)}:
{step_description}

IMPORTANT: Make the necessary code changes to implement this step. 
Ensure the changes are complete and consistent with existing code."""

    result = await aidertool.run(prompt)

    step_result = {
        "step_num": current_step + 1,
        "description": step_description,
        "success": result["success"],
        "output": result["output"][:2000],
        "files_changed": result["files_changed"],
    }

    return {
        "current_step": current_step + 1,
        "step_results": state["step_results"] + [step_result],
        "task": {
            "status": TaskStatus.CODING,
            "current_step": current_step + 1,
        },
    }


async def apply_fix(state: AgentState, fix_description: str, files: list[str] = None) -> dict:
    """Apply a specific fix (usually called after browser inspection finds issues)."""
    workspace = Path(state["workspace_path"])
    aidertool = AiderTool(workspace)

    prompt = f"""Fix the following issue in the project:

Issue: {fix_description}

{f'Relevant files: {chr(10).join(files)}' if files else ''}

Apply the fix carefully, ensuring it doesn't break existing functionality."""

    result = await aidertool.run(prompt)

    return {
        "step_results": state["step_results"] + [{
            "type": "fix",
            "description": fix_description,
            "success": result["success"],
            "files_changed": result["files_changed"],
            "output": result["output"][:1000],
        }],
    }