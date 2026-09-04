"""Test fixtures for TickerFlow (market-chatter) tests.

Uses SQLite with aiosqlite for isolated test databases.
"""

from __future__ import annotations

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from src.database import Base
from src.models.collection_run import CollectionRun
from src.models.price_bar import PriceBarRecord
from src.models.quota_usage import QuotaUsage
from src.models.raw_content import RawContent
from src.models.source_snapshot import SourceSnapshot
from src.models.ticker_daily_metric import TickerDailyMetric
from src.services.market_chatter.cache import JsonCache
from src.services.market_chatter.collection_service import CollectionService
from src.services.market_chatter.providers import FixturePriceProvider, FixtureProvider

MARKET_CHATTER_TABLES = [
    CollectionRun.__table__,
    SourceSnapshot.__table__,
    TickerDailyMetric.__table__,
    PriceBarRecord.__table__,
    QuotaUsage.__table__,
    RawContent.__table__,
]


async def _build_test_engine(db_path: str) -> AsyncEngine:
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(sync_conn, tables=MARKET_CHATTER_TABLES)
        )
    return engine


def _build_session_factory(engine: AsyncEngine) -> async_sessionmaker:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def service(tmp_path):
    from src.config import Settings

    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{tmp_path}/market_chatter.db",
        sentiment_provider="fixture",
        price_provider="fixture",
        redis_url="",
        _env_file=None,
    )
    engine = await _build_test_engine(f"{tmp_path}/market_chatter.db")
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
async def quota_session_factory(tmp_path) -> async_sessionmaker:
    engine = await _build_test_engine(f"{tmp_path}/quota.db")
    yield _build_session_factory(engine)
    await engine.dispose()
