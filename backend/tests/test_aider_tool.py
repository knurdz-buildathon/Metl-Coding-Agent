import pytest
from app.agents.tools.aider_tool import AiderTool
from pathlib import Path
import tempfile


@pytest.mark.asyncio
async def test_aider_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        tool = AiderTool(Path(tmpdir))
        assert tool.workspace_path == Path(tmpdir)
        assert tool.llm_provider == "openai"  # default changed to openai for Azure Foundry


@pytest.mark.asyncio
async def test_parse_changed_files():
    tool = AiderTool(Path("/tmp"))
    output = "Creating src/app/page.tsx\nUpdating package.json\nAdded src/lib/utils.ts"
    files = tool._parse_changed_files(output)
    assert "src/app/page.tsx" in files
    assert "package.json" in files
    assert "src/lib/utils.ts" in files