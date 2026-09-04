"""Speaker-ticker aggregation model - per-channel ticker stats."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database import Base


class SpeakerTickerAggregation(Base):
    __tablename__ = "speaker_ticker_aggregation"
    __table_args__ = (
        UniqueConstraint("channel_id", "ticker", name="uq_speaker_ticker_agg_channel_ticker"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    total_mentions: Mapped[int] = mapped_column(Integer, default=0)
    explicit_mentions: Mapped[int] = mapped_column(Integer, default=0)
    implicit_mentions: Mapped[int] = mapped_column(Integer, default=0)
    avg_sentiment: Mapped[float | None] = mapped_column(Float)  # -1 to +1
    weighted_relevance: Mapped[float | None] = mapped_column(Float)
    last_mentioned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    channel = relationship("Channel", back_populates="speaker_ticker_aggregations")
