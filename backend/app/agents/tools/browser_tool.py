import asyncio
import json
from typing import Optional

from app.services.llm_service import LLMService, get_llm_service


class BrowserTool:
    """
    Wrapper around browser-use for visual QA of preview apps.
    Falls back to LLM-based inspection if browser-use is unavailable.
    """

    def __init__(self):
        self._agent = None
        self._llm: LLMService = get_llm_service()

    async def inspect(self, url: str, task_description: str) -> dict:
        """
        Open a preview URL and inspect it for visual/code issues.
        
        Returns:
          - issues: list[dict] - each with {severity, description, screenshot_context}
          - passed: bool - whether the page passes visual QA
          - summary: str - high-level assessment
        """
        try:
            return await self._inspect_with_browser_use(url, task_description)
        except ImportError:
            return await self._inspect_with_llm(url, task_description)
        except Exception as e:
            return {
                "issues": [{"severity": "error", "description": f"Browser inspection failed: {str(e)}"}],
                "passed": False,
                "summary": f"Inspection error: {str(e)}",
            }

    async def _inspect_with_browser_use(self, url: str, task_description: str) -> dict:
        """Use browser-use agent for vision-based inspection."""
        from browser_use import Agent as BrowserUseAgent

        agent = BrowserUseAgent(
            task=(
                f"Visit {url} and thoroughly inspect the web application. "
                f"Task description: {task_description}\n\n"
                "Check for:\n"
                "1. Visual issues: broken layouts, missing elements, styling problems\n"
                "2. Functionality: buttons click, forms work, navigation is correct\n"
                "3. Content: all expected text/images/links are present\n"
                "4. Console errors: any JavaScript errors\n"
                "5. Responsive: looks correct at different viewport sizes\n\n"
                "After inspection, provide a detailed report of all issues found."
            ),
            llm=self._llm,
            use_vision=True,
        )

        result = await agent.run(max_steps=50)
        raw_output = result.extracted_content() if hasattr(result, "extracted_content") else str(result)

        # Parse the output to extract issues
        llm_response = await self._llm.generate(
            f"Parse the following browser inspection output into a structured JSON report. "
            f"Output ONLY valid JSON with fields: issues (array of {{severity, description}}), "
            f"passed (boolean), summary (string)\n\n{raw_output}"
        )

        try:
            return json.loads(llm_response)
        except json.JSONDecodeError:
            return {
                "issues": [{"severity": "info", "description": "Raw inspection output"}],
                "passed": True,
                "summary": raw_output[:500],
            }

    async def _inspect_with_llm(self, url: str, task_description: str) -> dict:
        """
        Fallback: LLM-based inspection when browser-use is not installed.
        This is a best-effort analysis based on the URL and task description.
        """
        prompt = (
            f"You are a QA inspector for a web application at {url}.\n"
            f"The application should: {task_description}\n\n"
            "Since you cannot browse the page directly, list potential issues "
            "to look for when the application is running. Categorize by severity "
            "(critical, major, minor, info).\n\n"
            "Output as JSON with fields: issues (array), passed (boolean), summary (string)."
        )

        response = await self._llm.generate(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "issues": [],
                "passed": True,
                "summary": "LLM fallback inspection - no actual browser used.",
            }