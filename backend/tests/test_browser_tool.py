import pytest
from app.agents.tools.browser_tool import BrowserTool


@pytest.mark.asyncio
async def test_browser_init():
    tool = BrowserTool()
    assert tool is not None


@pytest.mark.asyncio
async def test_llm_fallback_inspection():
    tool = BrowserTool()
    result = await tool._inspect_with_llm(
        url="http://localhost:3000",
        task_description="Build a landing page",
    )
    assert "issues" in result
    assert "passed" in result
    assert "summary" in result