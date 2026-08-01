"""PriceBarRecord model — cached daily price bars."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class PriceBarRecord(Base):
    __tablename__ = "price_bars"
    __table_args__ = (
        UniqueConstraint("symbol", "trade_date", name="uq_price_bar"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    close: Mapped[float] = mapped_column(Float)
    provider: Mapped[str] = mapped_column(String(32))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
