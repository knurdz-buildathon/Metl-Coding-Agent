import base64
from pathlib import Path

from app.agents.state import AgentState, get_task, task_update
from app.models import TaskStatus
from app.agents.tools.browser_tool import BrowserTool
from app.agents.tools.preview_tool import PreviewTool


async def inspect_preview_node(state: AgentState) -> dict:
    workspace = Path(state["workspace_path"])
    task = get_task(state)

    if not (workspace / "package.json").exists():
        return {
            "preview_url": None,
            "step_results": state["step_results"] + [{
                "type": "inspection",
                "issues": [],
                "passed": True,
                "summary": "No package.json found; skipping browser preview for non-Node project.",
            }],
            "task": task_update(state, status=TaskStatus.CODING),
        }

    preview = PreviewTool(workspace, port=4000)
    try:
        url = await preview.start(framework="nextjs")
    except (FileNotFoundError, RuntimeError) as e:
        return {
            "preview_url": None,
            "step_results": state["step_results"] + [{
                "type": "inspection",
                "issues": [{"severity": "major", "description": str(e)}],
                "passed": False,
                "summary": f"Preview server unavailable: {e}",
            }],
            "task": task_update(state, status=TaskStatus.CODING),
        }

    inspector = BrowserTool()
    result = await inspector.inspect(url, task.prompt)

    screenshots = []
    if "screenshots" in result:
        for scr in result["screenshots"]:
            if isinstance(scr, bytes):
                screenshots.append(base64.b64encode(scr).decode("utf-8"))
            elif isinstance(scr, str):
                screenshots.append(scr)

    browser_actions = result.get("actions", [])

    await preview.stop()

    issues = result.get("issues", [])
    has_issues = any(i.get("severity") in ("critical", "major") for i in issues)

    return {
        "preview_url": url,
        "step_results": state["step_results"] + [{
            "type": "inspection",
            "issues": issues,
            "passed": result.get("passed", True),
            "summary": result.get("summary", ""),
            "screenshots": screenshots,
            "browser_actions": browser_actions,
        }],
        "task": task_update(
            state,
            status=TaskStatus.INSPECTING if has_issues else TaskStatus.CODING,
        ),
    }


def has_issues_decision(state: AgentState) -> str:
    last_result = state["step_results"][-1] if state["step_results"] else {}
    issues = last_result.get("issues", [])
    critical = [i for i in issues if i.get("severity") in ("critical", "major")]
    if critical:
        return "fix"
    return "continue"