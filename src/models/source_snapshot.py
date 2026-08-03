"""SourceSnapshot model — raw sentiment snapshots per source."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class SourceSnapshot(Base):
    __tablename__ = "source_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    collection_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    company_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source: Mapped[str] = mapped_column(String(16), index=True)
    found: Mapped[bool] = mapped_column(default=True)
    buzz_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    mentions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    bullish_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    bearish_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    trend: Mapped[str | None] = mapped_column(String(32), nullable=True)
    unique_posts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coverage_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
