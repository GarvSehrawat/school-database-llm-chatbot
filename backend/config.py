"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "School Database LLM Chatbot"
    app_env: str = "development"
    debug: bool = True

    database_url: str = "sqlite:///./school.db"
    sql_echo: bool = False

    # Azure OpenAI configuration
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_chat_deployment: str | None = None

    # LLM behavior
    llm_enabled: bool = False
    llm_temperature: float = 0.0
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def azure_openai_configured(self) -> bool:
        """Return whether all required Azure OpenAI settings are present."""

        return bool(
            self.azure_openai_api_key
            and self.azure_openai_endpoint
            and self.azure_openai_chat_deployment
        )


@lru_cache
def get_settings() -> Settings:
    """Return one cached Settings instance for the application."""

    return Settings()


settings = get_settings()