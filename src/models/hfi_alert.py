"""HfiAlert model — rule-based alerts from content processing."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

HfiAlertTypeEnum = Enum(
    "new_filing", "new_company_mention", "new_thesis",
    "high_conviction", "portfolio_change", "daily_digest_ready",
    name="hfi_alert_type",
)

HfiAlertSeverityEnum = Enum("low", "medium", "high", "critical", name="hfi_alert_severity")


class HfiAlert(Base):
    __tablename__ = "hfi_alerts"
    __table_args__ = (
        CheckConstraint("score BETWEEN 0 AND 100", name="chk_hfi_alert_score_range"),
        Index("idx_hfi_alerts_user_unread", "user_id", "is_read", "created_at"),
        Index(
            "idx_hfi_alerts_investor",
            "investor_id",
            postgresql_where="investor_id IS NOT NULL",
        ),
        Index("idx_hfi_alerts_type", "alert_type"),
        Index(
            "idx_hfi_alerts_severity",
            "user_id",
            "severity",
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
    content_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_items.id", ondelete="SET NULL"), nullable=True
    )
    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hfi_reports.id", ondelete="SET NULL"), nullable=True
    )
    alert_type: Mapped[str] = mapped_column(HfiAlertTypeEnum, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        HfiAlertSeverityEnum, nullable=False, default="medium"
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    extra_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="hfi_alerts")
    investor: Mapped["Investor | None"] = relationship(
        "Investor", back_populates="alerts"
    )
    report: Mapped["HfiReport | None"] = relationship("HfiReport", back_populates="alerts")
