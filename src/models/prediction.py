"""Prediction model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False, index=True
    )
    segment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transcript_segments.id"),
        nullable=True,
        index=True,
    )
    theme_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("theme_hierarchy.id"),
        nullable=True,
        index=True,
    )
    ticker: Mapped[str | None] = mapped_column(String(20), index=True)
    prediction_text: Mapped[str] = mapped_column(Text, nullable=False)
    direction: Mapped[str | None] = mapped_column(
        String(50)
    )  # bullish | bearish | neutral (FinBERT-overridden)
    llm_direction: Mapped[str | None] = mapped_column(
        String(50)
    )  # Original LLM output (audit trail)
    finbert_confidence: Mapped[float | None] = mapped_column(Float)  # FinBERT max(P), 0-1
    confidence: Mapped[float | None] = mapped_column(Float)  # 0-1
    timeframe_hint: Mapped[str | None] = mapped_column(
        String(100)
    )  # short-term | long-term | earnings
    extracted_by: Mapped[str | None] = mapped_column(String(100))  # LLM model used
    accurate: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # NULL until evaluated
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    video = relationship("Video", back_populates="predictions")
    segment = relationship("TranscriptSegment")
    theme = relationship("ThemeHierarchy", back_populates="predictions")
    performance_records = relationship(
        "PerformanceRecord", back_populates="prediction", lazy="selectin"
    )
