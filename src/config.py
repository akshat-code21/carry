"""Application configuration via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration. Values loaded from .env or environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = (
        "postgresql+asyncpg://yt_chatter:yt_chatter_dev@localhost:5432/yt_chatter"
    )
    database_url_sync: str = (
        "postgresql://yt_chatter:yt_chatter_dev@localhost:5432/yt_chatter"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # YouTube Data API v3
    youtube_api_key: str = ""

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # OpenAI (for embeddings and chat)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # FRED
    fred_api_key: str = ""

    # Embedding
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 384

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
