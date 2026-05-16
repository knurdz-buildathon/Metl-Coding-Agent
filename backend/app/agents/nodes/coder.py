import asyncio
import os
from pathlib import Path

from app.agents.state import AgentState, get_task, task_update
from app.models import TaskStatus
from app.agents.tools.aider_tool import AiderTool
from app.agents.tools.fs_tool import FsTool
from app.agents.prompts import CODER_SYSTEM_PROMPT


async def execute_coding_step(state: AgentState) -> dict:
    task = get_task(state)
    workspace = Path(state["workspace_path"])
    aidertool = AiderTool(workspace)
    fstool = FsTool(workspace)

    current_step = state["current_step"]
    steps = task.plan.steps

    if current_step >= len(steps):
        return {"errors": ["No more steps to execute"]}

    step_description = steps[current_step]

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

    loop = asyncio.get_running_loop()

    # Capture pre-state: git diff baseline
    pre_diff = await _capture_git_diff(workspace, loop)
    pre_files = set(existing_files)

    result = await aidertool.run(prompt)

    # Capture post-state
    post_files = set(fstool.list_files())
    post_diff = await _capture_git_diff(workspace, loop)

    new_files = list(post_files - pre_files)
    changed_files = list(post_files & pre_files)

    # Use git to find modified files more reliably
    modified_files = result.get("files_changed", []) or new_files
    all_changed = list(set(modified_files + new_files))

    step_result = {
        "step_num": current_step + 1,
        "description": step_description,
        "success": result["success"],
        "output": result["output"][:2000],
        "files_changed": all_changed,
        "new_files": new_files,
        "diff": post_diff[:5000] if post_diff else "",
    }

    # Emit events for each changed file
    for fpath in all_changed:
        try:
            file_diff = await _capture_git_diff(workspace, loop, fpath)
        except Exception:
            file_diff = ""

    return {
        "current_step": current_step + 1,
        "step_results": state["step_results"] + [step_result],
        "task": task_update(
            state,
            status=TaskStatus.CODING,
            current_step=current_step + 1,
        ),
    }


async def apply_fix(state: AgentState, fix_description: str, files: list[str] = None) -> dict:
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


async def _capture_git_diff(workspace: Path, loop, file_path: str = "") -> str:
    try:
        if file_path:
            raw = await loop.run_in_executor(
                None,
                lambda: os.popen(f"cd {workspace} && git diff -- {file_path} 2>/dev/null").read(),
            )
        else:
            raw = await loop.run_in_executor(
                None,
                lambda: os.popen(f"cd {workspace} && git diff 2>/dev/null").read(),
            )
        return raw
    except Exception:
        return ""