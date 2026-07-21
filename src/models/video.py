"""Video model."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database import Base


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False, index=True
    )
    youtube_video_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_sec: Mapped[int | None] = mapped_column(Integer)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000))
    view_count: Mapped[int | None] = mapped_column(BigInteger)
    transcript_status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # pending | fetched | failed
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    channel = relationship("Channel", back_populates="videos")
    transcript_segments = relationship(
        "TranscriptSegment", back_populates="video", lazy="selectin"
    )
    theme_mentions = relationship("ThemeMention", back_populates="video", lazy="selectin")
    predictions = relationship("Prediction", back_populates="video", lazy="selectin")
    performance_records = relationship(
        "PerformanceRecord", back_populates="video", lazy="selectin"
    )
