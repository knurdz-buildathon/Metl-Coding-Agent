from app.agents.state import AgentState
from app.models import TaskStatus
from app.agents.tools.browser_tool import BrowserTool
from app.agents.tools.preview_tool import PreviewTool
from pathlib import Path


async def inspect_preview_node(state: AgentState) -> dict:
    """Start a preview server and inspect with browser-use."""
    workspace = Path(state["workspace_path"])
    task = state["task"]
    
    # Start preview server
    preview = PreviewTool(workspace, port=4000)
    url = await preview.start(framework="nextjs")
    
    # Inspect with browser-use
    inspector = BrowserTool()
    result = await inspector.inspect(url, task.prompt)
    
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
        }],
        "task": {
            "status": TaskStatus.INSPECTING if has_issues else TaskStatus.CODING,
        },
    }


def has_issues_decision(state: AgentState) -> str:
    """Decide if we need to fix issues or move on."""
    last_result = state["step_results"][-1] if state["step_results"] else {}
    issues = last_result.get("issues", [])
    critical = [i for i in issues if i.get("severity") in ("critical", "major")]
    if critical:
        return "fix"
    return "continue"