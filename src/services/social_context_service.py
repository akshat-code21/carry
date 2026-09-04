"""Social context service — TickerFlow (Reddit/X/News) sentiment for yt-chatter surfaces.

Bridges the YouTube-side search/ticker endpoints with the TickerFlow
CollectionService stashed in ``app.state.tickerflow_service``. All fetches are
on-demand (triggering collection when needed) but bounded by a per-ticker
timeout so search latency degrades gracefully; CollectionService's own
caching and quota management apply underneath.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.ticker_daily_metric import TickerDailyMetric
from src.schemas import SocialCoverageStats, SocialTickerSnapshot
from src.schemas.market_chatter import MCTickerResponse, SourceName
from src.services.market_chatter.collection_service import CollectionService

logger = logging.getLogger(__name__)

# Bounded wait per ticker so pages don't hang indefinitely on slow collection runs.
FETCH_TIMEOUT_SECONDS_DETAIL = 25.0
FETCH_TIMEOUT_SECONDS_CARD = 10.0
# TickerFlow only accepts 7 or 30 day periods.
PERIOD_DAYS_CARD = 7
PERIOD_DAYS_DETAIL = 30
# Chart is anchored on Reddit (the heaviest-weighted social source).
CHART_SOURCE = SourceName.REDDIT
# Cap parallel on-demand collections when enriching a list of tickers.
MAX_CONCURRENT_FETCHES = 4


def snapshot_from_response(response: MCTickerResponse) -> SocialTickerSnapshot:
    """Condense a full MCTickerResponse into the compact search-card shape."""
    mentions_values = [s.mentions for s in response.sources if s.mentions is not None]
    total_mentions = sum(mentions_values) if mentions_values else None

    sentiment_values = [
        s.sentiment_score for s in response.sources if s.sentiment_score is not None
    ]
    bullish_values = [s.bullish_pct for s in response.sources if s.bullish_pct is not None]
    bearish_values = [s.bearish_pct for s in response.sources if s.bearish_pct is not None]
    buzz_values = [s.buzz_score for s in response.sources if s.buzz_score is not None]

    return SocialTickerSnapshot(
        symbol=response.symbol,
        data_status=response.data_status,
        as_of=response.as_of,
        signal=response.signal,
        sources=list(response.sources),
        total_mentions=total_mentions,
        buzz_score=round(sum(buzz_values) / len(buzz_values), 1) if buzz_values else None,
        sentiment_score=(
            round(sum(sentiment_values) / len(sentiment_values), 3) if sentiment_values else None
        ),
        bullish_pct=(
            round(sum(bullish_values) / len(bullish_values), 1) if bullish_values else None
        ),
        bearish_pct=(
            round(sum(bearish_values) / len(bearish_values), 1) if bearish_values else None
        ),
    )


class SocialContextService:
    """On-demand TickerFlow social-sentiment fetcher with graceful degradation."""

    def __init__(self, service_getter: Callable[[], CollectionService | None]) -> None:
        self._service_getter = service_getter

    def _service(self) -> CollectionService | None:
        try:
            return self._service_getter()
        except Exception:  # noqa: BLE001 — app.state may be absent in some contexts
            return None

    async def get_ticker(
        self,
        symbol: str,
        period_days: int = PERIOD_DAYS_DETAIL,
        timeout: float | None = None,
    ) -> MCTickerResponse | None:
        """Fetch the full TickerFlow response for a symbol, or None on failure."""
        service = self._service()
        if service is None:
            logger.debug("social_context: TickerFlow service not initialised")
            return None
        normalized = symbol.strip().upper()
        effective_timeout = (
            timeout
            if timeout is not None
            else (
                FETCH_TIMEOUT_SECONDS_DETAIL
                if period_days == PERIOD_DAYS_DETAIL
                else FETCH_TIMEOUT_SECONDS_CARD
            )
        )
        try:
            return await asyncio.wait_for(
                service.ticker_response(normalized, CHART_SOURCE, period_days),
                timeout=effective_timeout,
            )
        except TimeoutError:
            logger.warning(
                "social_context: fetch timed out for %s (after %.1fs)",
                normalized,
                effective_timeout,
            )
            return None
        except Exception as exc:  # noqa: BLE001 — unsupported/unknown tickers are expected
            logger.debug("social_context: no social data for %s: %s", normalized, exc)
            return None

    async def get_snapshot(self, symbol: str) -> SocialTickerSnapshot | None:
        """Fetch the compact card snapshot for a single symbol."""
        response = await self.get_ticker(
            symbol, period_days=PERIOD_DAYS_CARD, timeout=FETCH_TIMEOUT_SECONDS_CARD
        )
        if response is None or not response.sources:
            return None
        return snapshot_from_response(response)

    async def get_snapshots(self, symbols: list[str]) -> dict[str, SocialTickerSnapshot]:
        """Fetch snapshots for many symbols with bounded concurrency."""
        unique = list(dict.fromkeys(s.strip().upper() for s in symbols if s and s.strip()))
        if not unique:
            return {}
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)

        async def _one(symbol: str) -> tuple[str, SocialTickerSnapshot | None]:
            async with semaphore:
                return symbol, await self.get_snapshot(symbol)

        pairs = await asyncio.gather(*(_one(s) for s in unique))
        return {symbol: snap for symbol, snap in pairs if snap is not None}


async def social_coverage_stats(
    db: AsyncSession,
    symbol: str,
    window_days: int,
    social_service: SocialContextService | None = None,
) -> SocialCoverageStats | None:
    """Aggregate stored TickerFlow daily metrics for a symbol over a window.

    When nothing is stored yet and a social service is available, one live
    collection is triggered (cached + quota-managed by CollectionService) and
    the metrics are re-read.
    """
    normalized = symbol.strip().upper()
    start = date.today() - timedelta(days=window_days - 1)

    async def _read_rows() -> list[TickerDailyMetric]:
        return list(
            (
                await db.scalars(
                    select(TickerDailyMetric).where(
                        TickerDailyMetric.symbol == normalized,
                        TickerDailyMetric.metric_date >= start,
                    )
                )
            ).all()
        )

    rows = await _read_rows()
    if not rows and social_service is not None:
        await social_service.get_ticker(normalized, period_days=PERIOD_DAYS_CARD)
        rows = await _read_rows()
    if not rows:
        return None

    by_source: dict[str, int] = {}
    total_mentions = 0
    weighted_sentiment = 0.0
    sentiment_weight = 0.0
    weighted_bullish = 0.0
    weighted_bearish = 0.0
    pct_weight = 0.0

    for row in rows:
        mentions = row.mentions or 0
        total_mentions += mentions
        by_source[row.source] = by_source.get(row.source, 0) + mentions
        if row.sentiment_score is not None and mentions > 0:
            weighted_sentiment += row.sentiment_score * mentions
            sentiment_weight += mentions
        if row.bullish_pct is not None and row.bearish_pct is not None and mentions > 0:
            weighted_bullish += row.bullish_pct * mentions
            weighted_bearish += row.bearish_pct * mentions
            pct_weight += mentions

    return SocialCoverageStats(
        symbol=normalized,
        mentions=total_mentions,
        bullish_pct=round(weighted_bullish / pct_weight, 1) if pct_weight else None,
        bearish_pct=round(weighted_bearish / pct_weight, 1) if pct_weight else None,
        sentiment_score=(
            round(weighted_sentiment / sentiment_weight, 3) if sentiment_weight else None
        ),
        by_source=by_source,
        available=total_mentions > 0,
    )
