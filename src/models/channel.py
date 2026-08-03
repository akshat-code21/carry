"""Channel model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    youtube_channel_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000))
    channel_type: Mapped[str] = mapped_column(
        String(50), default="individual", server_default="individual"
    )  # individual | institutional
    # WebSub / discovery tracking
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    websub_subscribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    websub_lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    websub_status: Mapped[str] = mapped_column(
        String(50), default="pending", server_default="pending"
    )  # pending | active | failed | disabled
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    videos = relationship("Video", back_populates="channel", lazy="selectin")
    speaker_ticker_aggregations = relationship(
        "SpeakerTickerAggregation", back_populates="channel", lazy="selectin"
    )
    activity_events = relationship("ActivityEvent", back_populates="channel", lazy="noload")
