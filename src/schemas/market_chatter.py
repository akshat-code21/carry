"""TickerFlow (market-chatter) Pydantic schemas.

Namespaced separately from the yt-chatter schemas to avoid the
TickerResponse naming collision.  The response model is named
MCTickerResponse here.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SourceName(StrEnum):
    REDDIT = "reddit"
    X = "x"
    NEWS = "news"


SOURCE_WEIGHTS: dict[SourceName, float] = {
    SourceName.REDDIT: 0.45,
    SourceName.X: 0.30,
    SourceName.NEWS: 0.25,
}


class DailyMetric(BaseModel):
    date: date
    mentions: int | None = Field(default=None, ge=0)
    buzz_score: float | None = Field(default=None, ge=0, le=100)
    sentiment_score: float | None = Field(default=None, ge=-1, le=1)
    bullish_pct: float | None = Field(default=None, ge=0, le=100)
    bearish_pct: float | None = Field(default=None, ge=0, le=100)


class ProviderSnapshot(BaseModel):
    """Normalized aggregate response returned by any sentiment provider."""

    model_config = ConfigDict(extra="forbid")

    symbol: str
    company_name: str | None = None
    source: SourceName
    found: bool = True
    buzz_score: float | None = Field(default=None, ge=0, le=100)
    mentions: int | None = Field(default=None, ge=0)
    sentiment_score: float | None = Field(default=None, ge=-1, le=1)
    bullish_pct: float | None = Field(default=None, ge=0, le=100)
    bearish_pct: float | None = Field(default=None, ge=0, le=100)
    trend: str | None = None
    unique_posts: int | None = Field(default=None, ge=0)
    coverage_count: int | None = Field(default=None, ge=0)
    daily_trend: list[DailyMetric] = Field(default_factory=list)
    fetched_at: datetime
    raw_payload: dict[str, Any]


class PriceBar(BaseModel):
    date: date
    close: float = Field(gt=0)


class SourceCard(BaseModel):
    source: SourceName
    status: str
    as_of: datetime | None = None
    sentiment_score: float | None = None
    buzz_score: float | None = None
    mentions: int | None = None
    bullish_pct: float | None = None
    bearish_pct: float | None = None
    trend: str | None = None
    coverage_count: int | None = None
    daily_mentions_available: bool = False
    message: str | None = None


class SignalSummary(BaseModel):
    label: str = "Phase 1 Signal"
    score: float | None = Field(default=None, ge=0, le=100)
    sentiment: float | None = Field(default=None, ge=0, le=100)
    attention: float | None = Field(default=None, ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    source_count: int = Field(ge=0, le=3)
    disclaimer: str = (
        "Aggregate vendor signal for informational use only; not investment advice."
    )


class ChartPoint(BaseModel):
    date: date
    mentions: int | None = None
    buzz_score: float | None = None
    close: float | None = None


class MCTickerResponse(BaseModel):
    """TickerFlow ticker response (named MCTickerResponse to avoid collision
    with the yt-chatter TickerResponse schema)."""

    symbol: str
    company_name: str | None = None
    data_status: str
    as_of: datetime | None = None
    signal: SignalSummary
    sources: list[SourceCard]
    chart_source: SourceName
    chart_metric: Literal["mentions", "buzz_score"]
    chart_period_days: int
    chart: list[ChartPoint]
    quota_remaining: int | None = None


class MCErrorResponse(BaseModel):
    detail: str
