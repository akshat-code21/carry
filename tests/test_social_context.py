"""Tests for the TickerFlow social-context bridge (search/ticker integration)."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from src.database import Base
from src.models.ticker_daily_metric import TickerDailyMetric
from src.schemas.market_chatter import MCTickerResponse
from src.services.market_chatter.cache import JsonCache
from src.services.market_chatter.collection_service import CollectionService
from src.services.market_chatter.providers import FixturePriceProvider, FixtureProvider
from src.services.social_context_service import (
    SocialContextService,
    snapshot_from_response,
    social_coverage_stats,
)

# Tables required by the social-context tests and the CollectionService they
# exercise. The full metadata contains PostgreSQL-only columns (ARRAY/JSONB)
# that SQLite cannot render, so we create an explicit subset.
SQLITE_TABLE_NAMES = (
    "collection_runs",
    "source_snapshots",
    "ticker_daily_metrics",
    "quota_usage",
    "price_bars",
)


async def _build_test_engine(db_path: str) -> AsyncEngine:
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", pool_pre_ping=True)
    tables = [Base.metadata.tables[name] for name in SQLITE_TABLE_NAMES]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))
    return engine


def _build_session_factory(engine: AsyncEngine) -> async_sessionmaker:
    return async_sessionmaker(engine, expire_on_commit=False)


def _make_settings(tmp_path, name: str):
    from src.config import Settings

    return Settings(
        database_url=f"sqlite+aiosqlite:///{tmp_path}/{name}.db",
        sentiment_provider="fixture",
        price_provider="fixture",
        redis_url="",
        _env_file=None,
    )


@pytest_asyncio.fixture
async def collection_service(tmp_path):
    settings = _make_settings(tmp_path, "collection")
    engine = await _build_test_engine(f"{tmp_path}/collection.db")
    instance = CollectionService(
        settings=settings,
        session_factory=_build_session_factory(engine),
        cache=JsonCache(),
        sentiment_provider=FixtureProvider(),
        price_provider=FixturePriceProvider(),
    )
    yield instance
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(tmp_path) -> async_sessionmaker:
    engine = await _build_test_engine(f"{tmp_path}/coverage.db")
    yield _build_session_factory(engine)
    await engine.dispose()


def _social_service(collection_service) -> SocialContextService:
    return SocialContextService(lambda: collection_service)


def test_snapshot_from_response_condenses_sources():
    response = MCTickerResponse.model_validate(
        {
            "symbol": "NVDA",
            "data_status": "fresh",
            "signal": {
                "score": 62.0,
                "sentiment": 70.0,
                "attention": 50.0,
                "confidence": 0.8,
                "source_count": 2,
            },
            "sources": [
                {
                    "source": "reddit",
                    "status": "ok",
                    "sentiment_score": 0.2,
                    "buzz_score": 40.0,
                    "mentions": 100,
                    "bullish_pct": 60.0,
                    "bearish_pct": 20.0,
                },
                {
                    "source": "news",
                    "status": "ok",
                    "sentiment_score": 0.4,
                    "buzz_score": 60.0,
                    "mentions": 50,
                    "bullish_pct": 70.0,
                    "bearish_pct": 10.0,
                },
            ],
            "chart_source": "reddit",
            "chart_metric": "mentions",
            "chart_period_days": 7,
            "chart": [],
        }
    )

    snap = snapshot_from_response(response)
    assert snap.symbol == "NVDA"
    assert snap.total_mentions == 150
    assert snap.buzz_score == 50.0
    assert snap.sentiment_score == pytest.approx(0.3)
    assert snap.bullish_pct == pytest.approx(65.0)
    assert snap.bearish_pct == pytest.approx(15.0)
    assert len(snap.sources) == 2
    assert snap.signal is not None and snap.signal.score == 62.0


@pytest.mark.asyncio
async def test_get_snapshot_uses_fixture_service(collection_service):
    service = _social_service(collection_service)
    snap = await service.get_snapshot("NVDA")
    assert snap is not None
    assert snap.symbol == "NVDA"
    assert snap.total_mentions is not None and snap.total_mentions > 0
    assert len(snap.sources) >= 1


@pytest.mark.asyncio
async def test_get_snapshots_dedupes(collection_service):
    service = _social_service(collection_service)
    result = await service.get_snapshots(["NVDA", "nvda", "MSFT"])
    assert set(result) == {"NVDA", "MSFT"}


@pytest.mark.asyncio
async def test_service_missing_returns_none():
    service = SocialContextService(lambda: None)
    assert await service.get_snapshot("NVDA") is None
    assert await service.get_snapshots(["NVDA"]) == {}


@pytest.mark.asyncio
async def test_social_coverage_stats_aggregates_by_source(session_factory):
    from datetime import UTC, date, datetime, timedelta

    async with session_factory() as session:
        today = date.today()
        now = datetime.now(UTC)
        session.add_all(
            [
                TickerDailyMetric(
                    symbol="AAPL",
                    source="reddit",
                    metric_date=today,
                    mentions=100,
                    sentiment_score=0.2,
                    bullish_pct=60.0,
                    bearish_pct=20.0,
                    observed_at=now,
                ),
                TickerDailyMetric(
                    symbol="AAPL",
                    source="news",
                    metric_date=today,
                    mentions=50,
                    sentiment_score=0.6,
                    bullish_pct=80.0,
                    bearish_pct=10.0,
                    observed_at=now,
                ),
                # Out-of-window row should be excluded
                TickerDailyMetric(
                    symbol="AAPL",
                    source="reddit",
                    metric_date=today - timedelta(days=60),
                    mentions=500,
                    sentiment_score=-0.9,
                    bullish_pct=5.0,
                    bearish_pct=90.0,
                    observed_at=now,
                ),
            ]
        )
        await session.commit()

    stats = await social_coverage_stats(session, "aapl", window_days=14)
    assert stats is not None
    assert stats.symbol == "AAPL"
    assert stats.mentions == 150
    assert stats.by_source == {"reddit": 100, "news": 50}
    # Mention-weighted: (0.2*100 + 0.6*50) / 150 = 0.333…
    assert stats.sentiment_score == pytest.approx(0.333, abs=0.01)
    # (60*100 + 80*50) / 150 = 66.67
    assert stats.bullish_pct == pytest.approx(66.7, abs=0.1)
    assert stats.available is True


@pytest.mark.asyncio
async def test_social_coverage_stats_empty_returns_none(session_factory):
    async with session_factory() as session:
        assert await social_coverage_stats(session, "ZZZZ", window_days=14) is None
