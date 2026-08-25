"""Investor model — tracks a hedge fund / institutional investor for 13F monitoring."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Investor(Base):
    __tablename__ = "investors"
    __table_args__ = (
        Index("idx_investors_user_id", "user_id"),
        Index("idx_investors_active", "user_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    cik_number: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="investors")
    sources: Mapped[list["HfiSource"]] = relationship(
        "HfiSource", back_populates="investor", cascade="all, delete-orphan"
    )
    content_items: Mapped[list["ContentItem"]] = relationship(
        "ContentItem", back_populates="investor", cascade="all, delete-orphan"
    )
    extracted_mentions: Mapped[list["ExtractedMention"]] = relationship(
        "ExtractedMention", back_populates="investor", cascade="all, delete-orphan"
    )
    portfolio_changes: Mapped[list["PortfolioChange"]] = relationship(
        "PortfolioChange", back_populates="investor", cascade="all, delete-orphan"
    )
    reports: Mapped[list["HfiReport"]] = relationship("HfiReport", back_populates="investor")
    alerts: Mapped[list["HfiAlert"]] = relationship("HfiAlert", back_populates="investor")
