"""Application configuration via pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration. Values loaded from .env or environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://yt_chatter:yt_chatter_dev@localhost:5432/yt_chatter"
    database_url_sync: str = "postgresql://yt_chatter:yt_chatter_dev@localhost:5432/yt_chatter"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # YouTube Data API v3
    youtube_api_key: str = ""

    # Supadata.ai (YouTube transcript API fallback)
    supadata_api_key: str = ""

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

    # YouTube WebSub (PubSubHubbub) - free Google hub
    websub_hub_url: str = "https://pubsubhubbub.appspot.com/subscribe"
    websub_secret: str = ""
    websub_lease_seconds: int = 864000  # 10 days (hub may clamp)
    websub_renew_margin_hours: int = 24

    # RSS fallback poll interval in hours (0 = disabled)
    discovery_fallback_poll_hours: int = 6

    # Comma-separated transcript retry delays in minutes after each failed attempt
    transcript_retry_delays_minutes: str = "0,15,60,360,1440"

    # Whisper model for local ASR fallback (tiny.en, base.en, small.en, etc.)
    whisper_model_size: str = "tiny.en"

    # ── TickerFlow / Market-Chatter ──────────────────────────────────────

    # Adanos social-sentiment API
    adanos_api_key: str | None = None
    adanos_plan: Literal["free", "hobby", "professional"] = "free"
    adanos_monthly_budget: int = 225
    adanos_base_url: str = "https://api.adanos.org"
    adanos_collection_days: int = 30

    # Provider selection (fixture = deterministic fake data for dev/tests)
    sentiment_provider: Literal["fixture", "adanos", "native_raw"] = "native_raw"
    price_provider: Literal["fixture", "yfinance_local"] = "yfinance_local"

    # Native Raw Ingestion Credentials & Controls
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "yt-chatter:v1.0 (by /u/market_chatter)"

    twitter_username: str = ""
    twitter_password: str = ""
    twitter_email: str = ""

    # CORS origins for the TickerFlow API (comma-separated)
    api_cors_origins: str = (
        "https://carry-fin.vercel.app,https://yt-chatter.vercel.app,http://localhost:3000"
    )
    api_cors_origin_regex: str = r"https://.*\.vercel\.app"

    # ── Authentication (Clerk) ───────────────────────────────────────────

    # Clerk Backend API secret key (sk_test_... / sk_live_...)
    clerk_secret_key: str = ""
    # PEM RSA public key for networkless JWT verification (from Clerk Dashboard → API Keys)
    clerk_jwt_key: str = ""
    # Comma-separated list of origins allowed in the token `azp` claim.
    # Leaving this empty disables azp validation (NOT recommended for production).
    clerk_authorized_parties: str = "http://localhost:3000,http://127.0.0.1:3000"
    # Clerk user ids that are auto-promoted to admin on first login
    # (comma-separated). The very first user to sign up also becomes admin.
    admin_clerk_user_ids: str = ""

    # ── Usage analytics ──────────────────────────────────────────────────

    # Master switch for usage-event / request-log recording
    analytics_enabled: bool = True
    # Retention (days) for raw event/request/LLM rows; daily rollups are kept forever
    analytics_retention_days: int = 180

    # Watchlist worker
    pilot_watchlist: str = "AAPL,NVDA"
    enable_watchlist_worker: bool = False

    # ── Properties ───────────────────────────────────────────────────────

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

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins, stripping trailing slashes."""
        origins: list[str] = []
        for raw in self.api_cors_origins.split(","):
            cleaned = raw.strip().rstrip("/")
            if cleaned and cleaned not in origins:
                origins.append(cleaned)
        return origins

    @property
    def clerk_authorized_parties_list(self) -> list[str]:
        """Parse comma-separated authorized parties into a list."""
        return [p.strip() for p in self.clerk_authorized_parties.split(",") if p.strip()]

    @property
    def admin_clerk_user_id_set(self) -> set[str]:
        """Parse comma-separated admin Clerk user ids into a set."""
        return {u.strip() for u in self.admin_clerk_user_ids.split(",") if u.strip()}

    @property
    def auth_enabled(self) -> bool:
        """True when a Clerk secret key is configured."""
        return bool(self.clerk_secret_key.strip())

    @property
    def pilot_symbols(self) -> list[str]:
        """Parse comma-separated pilot watchlist symbols."""
        return [
            symbol.strip().upper() for symbol in self.pilot_watchlist.split(",") if symbol.strip()
        ]

    def source_ttl_seconds(self, source: str) -> int:
        """Cache TTL for Adanos source snapshots. Free tier = 24h, pro = 15m/1h."""
        if self.adanos_plan != "professional":
            return 24 * 60 * 60
        return 15 * 60 if source == "news" else 60 * 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
