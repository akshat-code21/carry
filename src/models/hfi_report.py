"""HfiReport model — generated intelligence reports for investors."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

HfiReportTypeEnum = Enum(
    "investor_report", "daily_digest", "event_report",
    name="hfi_report_type",
)


class HfiReport(Base):
    __tablename__ = "hfi_reports"
    __table_args__ = (
        Index("idx_hfi_reports_user_id", "user_id"),
        Index(
            "idx_hfi_reports_investor_id",
            "investor_id",
            postgresql_where="investor_id IS NOT NULL",
        ),
        Index("idx_hfi_reports_type", "user_id", "report_type"),
        Index("idx_hfi_reports_generated", "user_id", "generated_at"),
        Index(
            "idx_hfi_reports_unread",
            "user_id",
            "is_read",
            postgresql_where="is_read = FALSE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    investor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investors.id", ondelete="SET NULL"), nullable=True
    )
    report_type: Mapped[str] = mapped_column(HfiReportTypeEnum, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    source_item_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list
    )
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="hfi_reports")
    investor: Mapped["Investor | None"] = relationship(
        "Investor", back_populates="reports"
    )
    alerts: Mapped[list["HfiAlert"]] = relationship("HfiAlert", back_populates="report")
