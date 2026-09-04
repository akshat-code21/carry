"""Tests for raw social/news collectors and NativeRawProvider."""

from __future__ import annotations

import pytest

from src.config import Settings
from src.schemas.market_chatter import SourceName
from src.services.market_chatter.collectors.news_collector import NewsCollector
from src.services.market_chatter.collectors.reddit_collector import RedditCollector
from src.services.market_chatter.collectors.stocktwits_collector import StockTwitsCollector
from src.services.market_chatter.collectors.twitter_collector import TwitterCollector
from src.services.market_chatter.providers import NativeRawProvider


@pytest.mark.asyncio
async def test_reddit_collector_returns_raw_items() -> None:
    settings = Settings(_env_file=None)
    collector = RedditCollector(settings)
    items = await collector.collect("NVDA", period_days=7)
    assert len(items) > 0
    assert any(item.symbol == "NVDA" for item in items)
    assert any("reddit:" in item.id for item in items)
    await collector.close()


@pytest.mark.asyncio
async def test_stocktwits_collector_returns_raw_items() -> None:
    collector = StockTwitsCollector()
    items = await collector.collect("AAPL", period_days=7)
    assert len(items) > 0
    assert any(item.symbol == "AAPL" for item in items)
    await collector.close()


@pytest.mark.asyncio
async def test_news_collector_returns_raw_items() -> None:
    collector = NewsCollector()
    items = await collector.collect("TSLA", period_days=7)
    assert len(items) > 0
    assert any(item.symbol == "TSLA" for item in items)
    assert len({item.id for item in items}) == len(items)  # All IDs unique
    assert len({item.content_hash for item in items}) == len(items)  # All hashes unique
    await collector.close()


@pytest.mark.asyncio
async def test_twitter_collector_returns_raw_items() -> None:
    settings = Settings(_env_file=None)
    collector = TwitterCollector(settings)
    items = await collector.collect("MSFT", period_days=7)
    assert len(items) > 0
    assert any(item.symbol == "MSFT" for item in items)
    assert len({item.id for item in items}) == len(items)  # All IDs unique
    assert len({item.content_hash for item in items}) == len(items)  # All hashes unique
    await collector.close()


@pytest.mark.asyncio
async def test_native_raw_provider_snapshot() -> None:
    settings = Settings(_env_file=None)
    provider = NativeRawProvider(settings)
    snapshot = await provider.get_ticker_snapshot("NVDA", SourceName.REDDIT, period_days=30)
    assert snapshot.symbol == "NVDA"
    assert snapshot.mentions is not None and snapshot.mentions > 0
    assert len(snapshot.daily_trend) == 30
    await provider.close()
