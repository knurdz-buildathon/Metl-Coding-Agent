from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # LLM Providers
    openai_api_key: Optional[str] = None
    openai_api_base: Optional[str] = None       # For Azure Foundry / custom OpenAI-compatible endpoints
    openai_api_version: Optional[str] = None    # e.g. "2026-04-01-preview"
    openai_org_id: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_generative_ai_api_key: Optional[str] = None

    # Preferred LLM for main agent loop
    # For Azure Foundry: LLM_PROVIDER=openai, LLM_MODEL=<deployment-name>
    # Requires OPENAI_API_BASE and OPENAI_API_VERSION to be set
    llm_provider: str = "openai"
    llm_model: str = "gpt-4.1"

    # LLM for Aider (can be different from main agent)
    aider_llm_provider: str = "openai"
    aider_llm_model: str = "gpt-4.1"

    # GitHub
    github_pat: str = ""
    github_webhook_secret: Optional[str] = None

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Feature Flags
    enable_cursor_sdk: bool = False
    cursor_api_key: Optional[str] = None
    enable_v0: bool = False
    v0_api_key: Optional[str] = None

    # Agent Config
    agent_max_steps: int = 500
    agent_checkpoint_interval: int = 5
    preview_base_url: str = "http://localhost:4000"

    # Server
    cors_origins: list[str] = ["*"]
    api_key: Optional[str] = None  # Auth key for control panel

    # Sandbox
    sandbox_base_dir: str = "/tmp/metl-workspaces"
    preview_port_range_start: int = 4000
    preview_port_range_end: int = 4999

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def validate(self):
        if not self.github_pat:
            raise ValueError("GITHUB_PAT is required")
        if not self.openai_api_key and not self.anthropic_api_key:
            raise ValueError("At least one LLM API key is required (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        if self.llm_provider == "openai" and self.openai_api_key:
            if self.openai_api_base and not self.openai_api_version:
                raise ValueError("OPENAI_API_VERSION is required when OPENAI_API_BASE is set")


settings = Settings()