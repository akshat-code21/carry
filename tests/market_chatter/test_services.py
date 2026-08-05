"""Tests for TickerFlow CollectionService."""

from __future__ import annotations

import pytest

from src.schemas.market_chatter import ProviderSnapshot, SourceName
from src.services.market_chatter.collection_service import (
    CollectionService,
    UnsupportedTickerError,
)
from src.services.market_chatter.providers import (
    FixtureProvider,
    ProviderUnavailable,
)


@pytest.mark.asyncio
async def test_fixture_collection_returns_three_source_signal(
    service: CollectionService,
) -> None:
    response = await service.ticker_response("NVDA", SourceName.REDDIT, 7)
    assert response.data_status == "fresh"
    assert response.signal.source_count == 3
    assert response.signal.score is not None
    assert len(response.sources) == 3
    assert response.chart
    assert response.chart_metric == "mentions"


@pytest.mark.asyncio
async def test_rejects_symbols_outside_configured_universe(
    service: CollectionService,
) -> None:
    with pytest.raises(UnsupportedTickerError):
        await service.ticker_response("INVALID123456", SourceName.REDDIT, 7)


class PartiallyUnavailableProvider(FixtureProvider):
    name = "adanos"

    async def get_ticker_snapshot(
        self, symbol: str, source: SourceName, period_days: int = 30
    ) -> ProviderSnapshot:
        if source == SourceName.X:
            raise ProviderUnavailable("X temporarily unavailable")
        return await super().get_ticker_snapshot(symbol, source, period_days)


@pytest.mark.asyncio
async def test_partial_source_failure_returns_partial_result(tmp_path) -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from src.config import Settings
    from src.database import Base
    from src.services.market_chatter.cache import JsonCache
    from src.services.market_chatter.providers import FixturePriceProvider

    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{tmp_path}/partial.db",
        adanos_monthly_budget=10,
        sentiment_provider="fixture",
        price_provider="fixture",
        redis_url="",
        _env_file=None,
    )
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    service = CollectionService(
        settings,
        async_sessionmaker(engine, expire_on_commit=False),
        JsonCache(),
        PartiallyUnavailableProvider(),
        FixturePriceProvider(),
    )
    response = await service.ticker_response("AAPL", SourceName.REDDIT, 7)
    assert response.data_status == "partial"
    assert response.signal.source_count == 2
    assert (
        next(card for card in response.sources if card.source == SourceName.X).status
        == "unavailable"
    )
    await engine.dispose()


class DuplicatePriceProvider:
    name = "duplicate_test_provider"

    async def get_daily_bars(self, symbol: str, period_days: int):
        from datetime import date

        from src.schemas.market_chatter import PriceBar

        # Intentionally return duplicate bars with the same trade_date
        return [
            PriceBar(date=date(2026, 6, 24), close=600.0),
            PriceBar(date=date(2026, 6, 24), close=601.5),
            PriceBar(date=date(2026, 6, 25), close=605.0),
        ]


@pytest.mark.asyncio
async def test_ensure_prices_handles_duplicate_dates(tmp_path) -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from src.config import Settings
    from src.database import Base
    from src.services.market_chatter.cache import JsonCache

    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{tmp_path}/dup.db",
        sentiment_provider="fixture",
        price_provider="fixture",
        redis_url="",
        _env_file=None,
    )
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    service = CollectionService(
        settings,
        async_sessionmaker(engine, expire_on_commit=False),
        JsonCache(),
        FixtureProvider(),
        DuplicatePriceProvider(),
    )
    response = await service.ticker_response("SOXX", SourceName.REDDIT, 7)
    assert response.symbol == "SOXX"
    assert len(response.chart) > 0
    await engine.dispose()
