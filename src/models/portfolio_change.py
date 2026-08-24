"""PortfolioChange model — tracks holding changes between 13F filing periods."""

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Enum, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

PortfolioChangeTypeEnum = Enum(
    "new_position", "increased", "decreased", "closed", "unchanged",
    name="portfolio_change_type",
)


class PortfolioChange(Base):
    __tablename__ = "portfolio_changes"
    __table_args__ = (
        Index("idx_portfolio_investor", "investor_id"),
        Index("idx_portfolio_ticker", "ticker_symbol"),
        Index("idx_portfolio_period", "investor_id", "filing_period"),
        Index("idx_portfolio_change", "change_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    investor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investors.id", ondelete="CASCADE"), nullable=False
    )
    content_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False
    )
    ticker_symbol: Mapped[str | None] = mapped_column(String, nullable=True)
    company_name: Mapped[str | None] = mapped_column(String, nullable=True)
    cusip: Mapped[str | None] = mapped_column(String, nullable=True)
    change_type: Mapped[str] = mapped_column(PortfolioChangeTypeEnum, nullable=False)
    shares_previous: Mapped[int] = mapped_column(BigInteger, default=0)
    shares_current: Mapped[int] = mapped_column(BigInteger, nullable=False)
    value_usd: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    percent_of_portfolio: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    filing_period: Mapped[str] = mapped_column(String, nullable=False)
    report_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    investor: Mapped["Investor"] = relationship("Investor", back_populates="portfolio_changes")
    content_item: Mapped["ContentItem"] = relationship(
        "ContentItem", back_populates="portfolio_changes"
    )
