"""TickerCache model — cached CUSIP/company-name → ticker symbol resolution."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class TickerCache(Base):
    """Cached CUSIP/company-name → ticker symbol resolution for 13F holdings."""

    __tablename__ = "ticker_cache"
    __table_args__ = (
        UniqueConstraint("company_name", name="uq_ticker_cache_company"),
        Index("idx_ticker_cache_cusip", "cusip", postgresql_where="cusip IS NOT NULL"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    cusip: Mapped[str | None] = mapped_column(String, nullable=True)
    ticker: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
