"""Tests for TickerFlow sentiment/price providers."""

from __future__ import annotations

from datetime import date

import httpx
import pytest

from src.config import Settings
from src.schemas.market_chatter import SourceName
from src.services.market_chatter.providers import (
    AdanosProvider,
    ProviderRateLimited,
    normalize_adanos_payload,
)


def test_normalizes_buzz_only_history_without_claiming_mentions() -> None:
    snapshot = normalize_adanos_payload(
        "NVDA",
        SourceName.X,
        {
            "ticker": "NVDA",
            "sentiment_score": 0.4,
            "buzz_score": 70,
            "trend_history": [51, 70],
        },
    )
    assert len(snapshot.daily_trend) == 2
    assert all(item.mentions is None for item in snapshot.daily_trend)
    assert snapshot.daily_trend[-1].buzz_score == 70


@pytest.mark.asyncio
async def test_adanos_provider_maps_rate_limits() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-API-Key"] == "test-key"
        return httpx.Response(429, json={"detail": "rate limited"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AdanosProvider(
        Settings(adanos_api_key="test-key", _env_file=None), client=client
    )
    with pytest.raises(ProviderRateLimited):
        await provider.get_ticker_snapshot("AAPL", SourceName.REDDIT)
    await client.aclose()


@pytest.mark.asyncio
async def test_adanos_provider_requests_explicit_history_window() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/reddit/stocks/v1/stock/TSLA"
        from_date = date.fromisoformat(request.url.params["from"])
        to_date = date.fromisoformat(request.url.params["to"])
        assert (to_date - from_date).days == 29
        return httpx.Response(
            200,
            json={
                "ticker": "TSLA",
                "buzz_score": 42,
                "mentions": 10,
                "daily_trend": [
                    {
                        "date": from_date.isoformat(),
                        "mentions": 2,
                        "buzz_score": 10,
                    },
                    {
                        "date": to_date.isoformat(),
                        "mentions": 8,
                        "buzz_score": 42,
                    },
                ],
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AdanosProvider(
        Settings(adanos_api_key="test-key", _env_file=None), client=client
    )
    snapshot = await provider.get_ticker_snapshot("TSLA", SourceName.REDDIT)
    assert snapshot.daily_trend[0].date <= snapshot.daily_trend[-1].date
    await client.aclose()
