from abc import ABC, abstractmethod
from typing import Any, Optional

from app.config import settings


class LLMService(ABC):
    """Abstract LLM interface for the agent."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        ...

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: type, **kwargs) -> Any:
        ...


class LiteLLMService(LLMService):
    """LiteLLM-based implementation supporting 100+ providers."""

    def __init__(self):
        self._has_litellm = False
        self._setup_providers()

    def _setup_providers(self):
        try:
            import litellm
            litellm.drop_params = True
            self._has_litellm = True
        except ImportError:
            self._has_litellm = False

        self.model = f"{settings.llm_provider}/{settings.llm_model}"

    def _get_acompletion_kwargs(self) -> dict:
        """Build kwargs for litellm.acompletion, including optional Azure/base overrides."""
        kwargs: dict[str, Any] = {}
        if settings.openai_api_base:
            kwargs["api_base"] = settings.openai_api_base
        if settings.openai_api_version:
            kwargs["api_version"] = settings.openai_api_version
        if settings.openai_org_id:
            kwargs["organization"] = settings.openai_org_id
        return kwargs

    async def generate(self, prompt: str, **kwargs) -> str:
        if not self._has_litellm:
            return f"[LiteLLM not installed. Prompt: {prompt[:80]}...]"
        import litellm

        acompletion_kwargs = self._get_acompletion_kwargs()
        acompletion_kwargs.update(kwargs)

        response = await litellm.acompletion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **acompletion_kwargs,
        )
        return response.choices[0].message.content or ""

    async def generate_structured(self, prompt: str, schema: type, **kwargs) -> Any:
        if not self._has_litellm:
            return schema()
        import litellm
        from litellm.types.utils import ResponseFormat

        acompletion_kwargs = self._get_acompletion_kwargs()
        acompletion_kwargs.update(kwargs)

        response = await litellm.acompletion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format=ResponseFormat(type="json_object"),
            **acompletion_kwargs,
        )
        content = response.choices[0].message.content or "{}"
        import json

        return schema(**json.loads(content))


class DummyLLMService(LLMService):
    """Fallback for testing when no API keys are configured."""

    async def generate(self, prompt: str, **kwargs) -> str:
        return f"[Dummy response to: {prompt[:50]}...]"

    async def generate_structured(self, prompt: str, schema: type, **kwargs) -> Any:
        return schema()


def get_llm_service() -> LLMService:
    if settings.openai_api_key or settings.anthropic_api_key:
        try:
            return LiteLLMService()
        except Exception:
            return DummyLLMService()
    return DummyLLMService()