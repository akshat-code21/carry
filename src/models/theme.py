"""Theme-related models: hierarchy, mentions, and ticker mappings."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database import Base


class ThemeHierarchy(Base):
    """Hierarchical theme taxonomy: sector → industry → theme → narrative."""

    __tablename__ = "theme_hierarchy"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("theme_hierarchy.id"), nullable=True, index=True
    )
    level: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # sector | industry | theme | narrative
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Self-referential relationship
    parent = relationship("ThemeHierarchy", remote_side="ThemeHierarchy.id", backref="children")

    # Relationships
    mentions = relationship("ThemeMention", back_populates="theme", lazy="selectin")
    ticker_mappings = relationship("ThemeTickerMapping", back_populates="theme", lazy="selectin")
    predictions = relationship("Prediction", back_populates="theme", lazy="selectin")


class ThemeMention(Base):
    """Records when a theme is mentioned in a video segment."""

    __tablename__ = "theme_mentions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id"), nullable=False, index=True
    )
    segment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transcript_segments.id"),
        nullable=False,
        index=True,
    )
    theme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("theme_hierarchy.id"),
        nullable=False,
        index=True,
    )
    sentiment: Mapped[str | None] = mapped_column(
        String(50)
    )  # bullish | bearish | neutral
    relevance_score: Mapped[float | None] = mapped_column(Float)  # 0-1
    mention_text: Mapped[str | None] = mapped_column(Text)  # Exact quote
    narrative: Mapped[str | None] = mapped_column(Text)  # Free-form description

    # Relationships
    video = relationship("Video", back_populates="theme_mentions")
    segment = relationship("TranscriptSegment", back_populates="theme_mentions")
    theme = relationship("ThemeHierarchy", back_populates="mentions")


class ThemeTickerMapping(Base):
    """Maps themes to ticker symbols (curated or LLM-generated)."""

    __tablename__ = "theme_ticker_mappings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    theme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("theme_hierarchy.id"),
        nullable=False,
        index=True,
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    relevance_score: Mapped[float | None] = mapped_column(Float)  # 0-1
    source: Mapped[str] = mapped_column(
        String(50), default="curated"
    )  # curated | llm
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    theme = relationship("ThemeHierarchy", back_populates="ticker_mappings")
