"""TickerDailyMetric model — daily sentiment/buzz time-series."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class TickerDailyMetric(Base):
    __tablename__ = "ticker_daily_metrics"
    __table_args__ = (UniqueConstraint("symbol", "source", "metric_date", name="uq_daily_metric"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    source: Mapped[str] = mapped_column(String(16), index=True)
    metric_date: Mapped[date] = mapped_column(Date, index=True)
    mentions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    buzz_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    bullish_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    bearish_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
