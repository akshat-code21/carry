"""Usage analytics models - raw event logs, request logs, LLM cost ledger, rollups."""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.database import Base

# JSONB on PostgreSQL, plain JSON elsewhere (e.g. test SQLite fixtures)
VariantJSON = JSON().with_variant(JSONB, "postgresql")


class UsageEvent(Base):
    """Raw product-analytics event (one row per tracked user action).

    ``event_type`` examples: search_performed, page_viewed, video_viewed,
    channel_viewed, theme_viewed, ticker_viewed, pipeline_triggered,
    chatter_refresh_requested, invite_redeemed, user_signed_up.
    ``source`` distinguishes user actions from system/Celery traffic.
    """

    __tablename__ = "usage_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="user")
    payload: Mapped[dict[str, Any]] = mapped_column(VariantJSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    __table_args__ = (Index("ix_usage_events_type_created", "event_type", "created_at"),)


class ApiRequestLog(Base):
    """One row per API request (written by the analytics middleware).

    Powers usage counts, error rates, latency monitoring and DAU/WAU/MAU.
    """

    __tablename__ = "api_request_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    # Route template with path params collapsed, e.g. /api/videos/{video_id}
    route_template: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    __table_args__ = (Index("ix_api_request_logs_created_user", "created_at", "user_id"),)


class LlmUsageLog(Base):
    """LLM / embedding cost ledger - one row per model call.

    Attributes real spend to users, features and days.
    """

    __tablename__ = "llm_usage_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # openai | anthropic
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    purpose: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # search_classify | embedding | claim_extraction ...
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    success: Mapped[bool] = mapped_column(nullable=False, default=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class DailyUserUsage(Base):
    """Per-user per-day counters, upserted atomically when events are recorded.

    Makes usage dashboards O(days×users) reads instead of raw-log scans.
    """

    __tablename__ = "daily_user_usage"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    api_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    searches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    search_zero_results: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    page_views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    video_views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    channel_views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    theme_views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ticker_views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expensive_ops: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    llm_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    llm_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PlatformDailyUsage(Base):
    """Platform-wide daily counters (all users combined)."""

    __tablename__ = "platform_daily_usage"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    active_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    api_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    searches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    search_zero_results: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    page_views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expensive_ops: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    llm_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    llm_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
