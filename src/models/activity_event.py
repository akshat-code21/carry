"""Activity event model — in-app feed for video detection/processing."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database import Base


class ActivityEvent(Base):
    """In-app notification / activity feed row.

    Uniqueness on (event_type, youtube_video_id) prevents duplicate spam from
    WebSub retries or concurrent poll + push races.
    """

    __tablename__ = "activity_events"
    __table_args__ = (
        UniqueConstraint(
            "event_type",
            "youtube_video_id",
            name="uq_activity_event_type_youtube_video",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # video_detected | video_processed | video_failed
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id"), nullable=False, index=True
    )
    video_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("videos.id"), nullable=True, index=True
    )
    youtube_video_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON().with_variant(JSONB, "postgresql"))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    channel = relationship("Channel", back_populates="activity_events")
    video = relationship("Video", back_populates="activity_events")
