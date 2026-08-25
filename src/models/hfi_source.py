"""HFI Source model — data sources (SEC 13F, website, RSS, etc.) for an investor."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

HfiSourceTypeEnum = Enum(
    "sec_13f",
    "website",
    "youtube",
    "rss",
    "twitter",
    "custom",
    name="hfi_source_type",
)


class HfiSource(Base):
    __tablename__ = "hfi_sources"
    __table_args__ = (
        Index("idx_hfi_sources_investor_id", "investor_id"),
        Index("idx_hfi_sources_type", "source_type"),
        Index(
            "idx_hfi_sources_active_check",
            "is_active",
            "last_checked_at",
            postgresql_where="is_active = TRUE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investors.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(HfiSourceTypeEnum, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str | None] = mapped_column(String, nullable=True)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_successful_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    check_frequency_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    investor = relationship("Investor", back_populates="sources")
    content_items = relationship(
        "ContentItem", back_populates="source", cascade="all, delete-orphan"
    )
