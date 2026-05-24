import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "gemini"   # gemini | openai

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    tavily_api_key: str = ""

    # Image generation: defaults to Pollinations (free, no auth). If FAL_KEY is
    # set, we'll use fal.ai Flux Schnell instead (faster + sharper).
    fal_api_key: str = ""
    image_gen_enabled: bool = True

    public_base_url: str = "http://localhost:8000"
    report_ttl_hours: int = 24

    allow_mock_fallback: bool = True

    @property
    def has_llm(self) -> bool:
        if self.llm_provider == "openai":
            return bool(self.openai_api_key)
        return bool(self.gemini_api_key)

    @property
    def has_search(self) -> bool:
        return bool(self.tavily_api_key)

    @property
    def resolved_base_url(self) -> str:
        """Prefer Render's auto-injected URL when present."""
        render_url = os.environ.get("RENDER_EXTERNAL_URL")
        if render_url:
            return render_url
        return self.public_base_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
