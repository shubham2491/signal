from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    tavily_api_key: str = ""

    public_base_url: str = "http://localhost:8000"
    report_ttl_hours: int = 24

    allow_mock_fallback: bool = True

    @property
    def has_llm(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_search(self) -> bool:
        return bool(self.tavily_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
