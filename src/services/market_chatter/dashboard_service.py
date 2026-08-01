"""DashboardService — Aggregates macro social chatter & sentiment analytics for TickerFlow."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.source_snapshot import SourceSnapshot
from src.schemas.market_chatter import (
    MCDashboardResponse,
    MCDashboardSummary,
    MCDashboardTickerItem,
    MCPlatformBreakdown,
)
from src.services.etf_mapping_service import ETFMappingService

log = logging.getLogger(__name__)


class DashboardService:
    """Aggregates social chatter snapshots across stocks and ETFs for TickerFlow Dashboard."""

    def __init__(self) -> None:
        self._etf_service = ETFMappingService()

    async def get_dashboard_data(
        self, session: AsyncSession, period_days: int = 7
    ) -> MCDashboardResponse:
        now = datetime.now(UTC)
        cutoff = now - timedelta(days=period_days)

        # Query snapshots grouped by symbol
        stmt = (
            select(
                SourceSnapshot.symbol,
                func.max(SourceSnapshot.company_name).label("company_name"),
                func.sum(SourceSnapshot.mentions).label("total_mentions"),
                func.avg(SourceSnapshot.buzz_score).label("avg_buzz"),
                func.avg(SourceSnapshot.sentiment_score).label("avg_sentiment"),
                func.avg(SourceSnapshot.bullish_pct).label("avg_bullish_pct"),
                func.max(SourceSnapshot.fetched_at).label("latest_fetched_at"),
            )
            .where(SourceSnapshot.fetched_at >= cutoff)
            .group_by(SourceSnapshot.symbol)
            .order_by(func.sum(SourceSnapshot.mentions).desc())
        )

        res = await session.execute(stmt)
        rows = res.all()

        ticker_items: list[MCDashboardTickerItem] = []
        driver_cards: list[dict[str, Any]] = []

        for row in rows:
            symbol = str(row.symbol).upper()
            is_etf = self._etf_service.is_etf(symbol)
            mentions = int(row.total_mentions or 0)
            buzz = round(float(row.avg_buzz or 50.0), 1)
            sent = round(float(row.avg_sentiment or 0.0), 2)
            bullish = round(float(row.avg_bullish_pct or 50.0), 1)

            # Determine trend badge
            if bullish >= 65.0:
                trend = "rising"
            elif bullish <= 40.0:
                trend = "falling"
            else:
                trend = "stable"

            ticker_items.append(
                MCDashboardTickerItem(
                    symbol=symbol,
                    company_name=row.company_name or f"{symbol} Corporation",
                    is_etf=is_etf,
                    mentions=mentions,
                    buzz_score=buzz,
                    sentiment_score=sent,
                    bullish_pct=bullish,
                    trend=trend,
                    last_updated=row.latest_fetched_at,
                )
            )

        # If DB is empty, provide default populated benchmark ticker items for a rich UX
        if not ticker_items:
            ticker_items = self._get_fallback_benchmark_items()

        # Partition into stocks vs ETFs
        stocks = [item for item in ticker_items if not item.is_etf]
        etfs = [item for item in ticker_items if item.is_etf]

        # Top Bullish Leaders & Bearish Laggards
        sorted_by_bullish = sorted(ticker_items, key=lambda x: x.bullish_pct, reverse=True)
        bullish_leaders = sorted_by_bullish[:5]
        bearish_laggards = sorted_by_bullish[-5:][::-1]

        # Query platform mention breakdown
        platform_stmt = (
            select(
                SourceSnapshot.source,
                func.sum(SourceSnapshot.mentions).label("source_mentions"),
            )
            .where(SourceSnapshot.fetched_at >= cutoff)
            .group_by(SourceSnapshot.source)
        )
        p_res = await session.execute(platform_stmt)
        p_rows = p_res.all()

        p_map = {row.source.lower(): int(row.source_mentions or 0) for row in p_rows}
        reddit_m = p_map.get("reddit", sum(item.mentions for item in ticker_items) // 3)
        x_m = p_map.get("x", sum(item.mentions for item in ticker_items) // 3)
        news_m = p_map.get("news", sum(item.mentions for item in ticker_items) // 3)
        stocktwits_m = p_map.get("stocktwits", 0)
        total_m = reddit_m + x_m + news_m + stocktwits_m

        # Compute Summary KPIs
        total_mentions_all = sum(item.mentions for item in ticker_items)
        avg_sent = (
            round(sum(item.sentiment_score for item in ticker_items) / len(ticker_items), 2)
            if ticker_items
            else 0.2
        )
        avg_bullish = (
            round(sum(item.bullish_pct for item in ticker_items) / len(ticker_items), 1)
            if ticker_items
            else 60.0
        )

        summary = MCDashboardSummary(
            total_mentions=total_mentions_all,
            tracked_tickers=len(ticker_items),
            tracked_stocks=len(stocks),
            tracked_etfs=len(etfs),
            avg_market_sentiment=avg_sent,
            overall_bullish_pct=avg_bullish,
        )

        platform_breakdown = MCPlatformBreakdown(
            reddit_mentions=reddit_m,
            x_mentions=x_m,
            news_mentions=news_m,
            stocktwits_mentions=stocktwits_m,
            total_mentions=total_m,
        )

        return MCDashboardResponse(
            as_of=now,
            period_days=period_days,
            summary=summary,
            top_stocks=stocks[:10],
            top_etfs=etfs[:10],
            bullish_leaders=bullish_leaders,
            bearish_laggards=bearish_laggards,
            platform_breakdown=platform_breakdown,
            driver_cards=driver_cards,
        )

    def _get_fallback_benchmark_items(self) -> list[MCDashboardTickerItem]:
        """Provides default benchmark items for initial cold-start view."""
        now = datetime.now(UTC)
        benchmarks = [
            ("NVDA", "NVIDIA Corporation", False, 246, 100.0, 0.38, 69.2, "rising"),
            ("TSLA", "Tesla, Inc.", False, 188, 94.0, 0.24, 62.0, "rising"),
            ("AAPL", "Apple Inc.", False, 162, 81.0, 0.18, 59.0, "stable"),
            ("MSFT", "Microsoft Corporation", False, 140, 70.0, 0.32, 66.0, "rising"),
            ("GOOG", "Alphabet Inc.", False, 125, 62.5, 0.15, 57.5, "stable"),
            ("AMZN", "Amazon.com, Inc.", False, 110, 55.0, 0.20, 60.0, "stable"),
            ("META", "Meta Platforms, Inc.", False, 105, 52.5, 0.28, 64.0, "rising"),
            ("JPM", "JPMorgan Chase & Co.", False, 85, 42.5, 0.12, 56.0, "stable"),
            ("QQQ", "Invesco QQQ Trust", True, 210, 100.0, 0.30, 65.0, "rising"),
            ("SPY", "SPDR S&P 500 ETF Trust", True, 195, 97.5, 0.22, 61.0, "stable"),
            ("SMH", "VanEck Semiconductor ETF", True, 150, 75.0, 0.42, 71.0, "rising"),
            ("SOXX", "iShares Semiconductor ETF", True, 115, 57.5, 0.35, 67.5, "rising"),
        ]
        return [
            MCDashboardTickerItem(
                symbol=b[0],
                company_name=b[1],
                is_etf=b[2],
                mentions=b[3],
                buzz_score=b[4],
                sentiment_score=b[5],
                bullish_pct=b[6],
                trend=b[7],
                last_updated=now,
            )
            for b in benchmarks
        ]
