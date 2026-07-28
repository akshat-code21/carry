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

    # Public base URL for WebSub callbacks (ngrok URL locally, real host in prod).
    # No trailing slash. Empty = skip WebSub subscribe (poll fallback only).
    public_base_url: str = ""

    # YouTube WebSub (PubSubHubbub) — free Google hub
    websub_hub_url: str = "https://pubsubhubbub.appspot.com/subscribe"
    websub_secret: str = ""
    websub_lease_seconds: int = 864000  # 10 days (hub may clamp)
    websub_renew_margin_hours: int = 24

    # RSS fallback poll interval in hours (0 = disabled)
    discovery_fallback_poll_hours: int = 6

    # Comma-separated transcript retry delays in minutes after each failed attempt
    transcript_retry_delays_minutes: str = "0,15,60,360,1440"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def websub_enabled(self) -> bool:
        """True when a public callback base URL is configured."""
        return bool(self.public_base_url.strip())

    @property
    def transcript_retry_delays(self) -> list[int]:
        """Parse transcript retry delays (minutes) into a list of ints."""
        raw = self.transcript_retry_delays_minutes.strip()
        if not raw:
            return [0, 15, 60, 360, 1440]
        delays: list[int] = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                delays.append(max(0, int(part)))
            except ValueError:
                continue
        return delays or [0, 15, 60, 360, 1440]


@lru_cache
def get_settings() -> Settings:
    return Settings()
