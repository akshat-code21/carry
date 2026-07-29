"""Sentiment and price data providers for TickerFlow.

Contains the protocol definitions, the Adanos API adapter, fixture
(fake-data) providers for local development, and builder functions.
"""

from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, date, datetime, timedelta
from typing import Protocol

import httpx

from src.config import Settings
from src.schemas.market_chatter import DailyMetric, PriceBar, ProviderSnapshot, SourceName


class ProviderError(Exception):
    pass


class ProviderRateLimited(ProviderError):
    pass


class ProviderUnavailable(ProviderError):
    pass


class MarketSentimentProvider(Protocol):
    name: str

    async def get_ticker_snapshot(
        self, symbol: str, source: SourceName, period_days: int = 30
    ) -> ProviderSnapshot: ...

    async def get_trending(
        self, source: SourceName, period_days: int = 7
    ) -> list[ProviderSnapshot]: ...

    async def get_market_snapshot(self, source: SourceName) -> ProviderSnapshot: ...

    async def close(self) -> None: ...


class PriceProvider(Protocol):
    name: str

    async def get_daily_bars(self, symbol: str, period_days: int) -> list[PriceBar]: ...


# ── Helpers ──────────────────────────────────────────────────────────────


def _number(payload: dict, *keys: str) -> float | int | None:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return value
    return None


def _daily_metrics(payload: dict) -> list[DailyMetric]:
    daily = payload.get("daily_trend")
    if isinstance(daily, list) and daily and isinstance(daily[0], dict):
        results: list[DailyMetric] = []
        for item in daily:
            raw_date = item.get("date")
            if not raw_date:
                continue
            try:
                results.append(
                    DailyMetric(
                        date=date.fromisoformat(str(raw_date)[:10]),
                        mentions=_number(item, "mentions"),
                        buzz_score=_number(item, "buzz_score"),
                        sentiment_score=_number(item, "sentiment_score"),
                        bullish_pct=_number(item, "bullish_pct"),
                        bearish_pct=_number(item, "bearish_pct"),
                    )
                )
            except (TypeError, ValueError):
                continue
        return results

    # Adanos may return a buzz-only trend_history array for a source.
    history = payload.get("trend_history")
    if not isinstance(history, list):
        return []
    start = date.today() - timedelta(days=len(history) - 1)
    return [
        DailyMetric(date=start + timedelta(days=index), buzz_score=value)
        for index, value in enumerate(history)
        if isinstance(value, int | float)
    ]


def normalize_adanos_payload(
    symbol: str, source: SourceName, payload: dict
) -> ProviderSnapshot:
    return ProviderSnapshot(
        symbol=symbol.upper(),
        company_name=payload.get("company_name"),
        source=source,
        found=payload.get("found", True),
        buzz_score=_number(payload, "buzz_score"),
        mentions=_number(payload, "mentions"),
        sentiment_score=_number(payload, "sentiment_score"),
        bullish_pct=_number(payload, "bullish_pct"),
        bearish_pct=_number(payload, "bearish_pct"),
        trend=payload.get("trend"),
        unique_posts=_number(payload, "unique_posts", "unique_tweets"),
        coverage_count=_number(payload, "subreddit_count", "source_count"),
        daily_trend=_daily_metrics(payload),
        fetched_at=datetime.now(UTC),
        raw_payload=payload,
    )


# ── Adanos Provider ─────────────────────────────────────────────────────


class AdanosProvider:
    """The only component allowed to make social/news HTTP calls."""

    name = "adanos"

    def __init__(
        self, settings: Settings, client: httpx.AsyncClient | None = None
    ) -> None:
        if not settings.adanos_api_key:
            raise ValueError("ADANOS_API_KEY is required when SENTIMENT_PROVIDER=adanos")
        self._base_url = settings.adanos_base_url.rstrip("/")
        self._api_key = settings.adanos_api_key
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=3.0),
            headers={"X-API-Key": self._api_key, "Accept": "application/json"},
        )
        self._owns_client = client is None

    def _url(self, source: SourceName, path: str) -> str:
        return f"{self._base_url}/{source.value}/stocks/v1{path}"

    @staticmethod
    def _date_window(period_days: int) -> dict[str, str]:
        to_date = datetime.now(UTC).date()
        from_date = to_date - timedelta(days=max(period_days, 1) - 1)
        return {"from": from_date.isoformat(), "to": to_date.isoformat()}

    async def _get(
        self, source: SourceName, path: str, params: dict | None = None
    ) -> dict | list:
        try:
            response = await self._client.get(
                self._url(source, path),
                params=params,
                headers={"X-API-Key": self._api_key, "Accept": "application/json"},
            )
        except httpx.TimeoutException as exc:
            raise ProviderUnavailable("Adanos request timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailable("Adanos request failed") from exc
        if response.status_code == 429:
            raise ProviderRateLimited("Adanos rate limit reached")
        if response.status_code >= 500:
            raise ProviderUnavailable(f"Adanos unavailable ({response.status_code})")
        if response.status_code >= 400:
            raise ProviderError(f"Adanos request rejected ({response.status_code})")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderError("Adanos returned invalid JSON") from exc
        if not isinstance(payload, (dict, list)):
            raise ProviderError("Adanos returned an unexpected response shape")
        return payload

    async def get_ticker_snapshot(
        self, symbol: str, source: SourceName, period_days: int = 30
    ) -> ProviderSnapshot:
        payload = await self._get(
            source,
            f"/stock/{symbol.upper()}",
            self._date_window(period_days),
        )
        if not isinstance(payload, dict):
            raise ProviderError("Adanos ticker response was not an object")
        return normalize_adanos_payload(symbol, source, payload)

    async def get_trending(
        self, source: SourceName, period_days: int = 7
    ) -> list[ProviderSnapshot]:
        payload = await self._get(source, "/trending", {"limit": 20})
        if not isinstance(payload, list):
            raise ProviderError("Adanos trending response was not a list")
        return [
            normalize_adanos_payload(str(item.get("ticker", "")), source, item)
            for item in payload
            if isinstance(item, dict) and item.get("ticker")
        ]

    async def get_market_snapshot(self, source: SourceName) -> ProviderSnapshot:
        payload = await self._get(source, "/market-sentiment")
        if not isinstance(payload, dict):
            raise ProviderError("Adanos market response was not an object")
        return normalize_adanos_payload("MARKET", source, payload)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()


# ── Fixture Providers (dev / test) ───────────────────────────────────────


class FixtureProvider:
    """Deterministic Adanos-compatible data for local development and tests."""

    name = "fixture"

    def _seed(self, symbol: str, source: SourceName) -> int:
        digest = hashlib.sha256(f"{symbol}:{source.value}".encode()).hexdigest()
        return int(digest[:8], 16)

    async def get_ticker_snapshot(
        self, symbol: str, source: SourceName, period_days: int = 30
    ) -> ProviderSnapshot:
        symbol = symbol.upper()
        seed = self._seed(symbol, source)
        today = date.today()
        base_mentions = 20 + seed % 120
        sentiment = round(((seed % 180) - 90) / 100, 2)
        daily = []
        for index in range(period_days):
            day_seed = seed + index * 29
            mentions = max(2, base_mentions + ((day_seed % 41) - 20))
            day_sentiment = max(
                -1.0, min(1.0, sentiment + ((index % 3) - 1) * 0.06)
            )
            daily.append(
                DailyMetric(
                    date=today - timedelta(days=period_days - 1 - index),
                    mentions=mentions,
                    buzz_score=round(min(100, mentions * 0.6), 1),
                    sentiment_score=round(day_sentiment, 2),
                    bullish_pct=round((day_sentiment + 1) * 50, 1),
                    bearish_pct=round((1 - day_sentiment) * 35, 1),
                )
            )
        payload = {
            "ticker": symbol,
            "company_name": f"{symbol} Holdings, Inc.",
            "found": True,
            "buzz_score": daily[-1].buzz_score,
            "mentions": sum(item.mentions or 0 for item in daily),
            "sentiment_score": sentiment,
            "bullish_pct": round((sentiment + 1) * 50, 1),
            "bearish_pct": round((1 - sentiment) * 35, 1),
            "trend": "rising" if daily[-1].mentions > daily[0].mentions else "stable",
            "unique_posts": base_mentions,
            "subreddit_count": 3 + seed % 8 if source == SourceName.REDDIT else None,
            "source_count": 3 + seed % 8 if source == SourceName.NEWS else None,
            "daily_trend": [item.model_dump(mode="json") for item in daily],
        }
        return normalize_adanos_payload(symbol, source, payload)

    async def get_trending(
        self, source: SourceName, period_days: int = 7
    ) -> list[ProviderSnapshot]:
        return [
            await self.get_ticker_snapshot(symbol, source)
            for symbol in ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN"]
        ]

    async def get_market_snapshot(self, source: SourceName) -> ProviderSnapshot:
        return await self.get_ticker_snapshot("MARKET", source)

    async def close(self) -> None:
        return None


class FixturePriceProvider:
    name = "fixture"

    async def get_daily_bars(self, symbol: str, period_days: int) -> list[PriceBar]:
        seed = int(hashlib.sha256(symbol.upper().encode()).hexdigest()[:8], 16)
        price = 70 + (seed % 360)
        today = date.today()
        bars: list[PriceBar] = []
        for offset in range(period_days - 1, -1, -1):
            trade_date = today - timedelta(days=offset)
            if trade_date.weekday() >= 5:
                continue
            movement = ((seed + offset * 11) % 13 - 6) / 100
            price = max(5, price * (1 + movement / 10))
            bars.append(PriceBar(date=trade_date, close=round(price, 2)))
        return bars


class YFinanceLocalPriceProvider:
    """Local-only Yahoo-backed price adapter. Never enable for a public product."""

    name = "yfinance_local"

    async def get_daily_bars(self, symbol: str, period_days: int) -> list[PriceBar]:
        def fetch() -> list[PriceBar]:
            import yfinance as yf

            history = yf.Ticker(symbol).history(
                period=f"{max(period_days + 7, 30)}d", interval="1d"
            )
            bars: list[PriceBar] = []
            for index, row in history.tail(period_days).iterrows():
                close = row.get("Close")
                if close is None:
                    continue
                bars.append(PriceBar(date=index.date(), close=round(float(close), 2)))
            return bars

        return await asyncio.to_thread(fetch)


# ── Builder functions ────────────────────────────────────────────────────


def build_sentiment_provider(settings: Settings) -> MarketSentimentProvider:
    if settings.sentiment_provider == "adanos":
        return AdanosProvider(settings)
    return FixtureProvider()


def build_price_provider(settings: Settings) -> PriceProvider:
    if settings.price_provider == "yfinance_local":
        return YFinanceLocalPriceProvider()
    return FixturePriceProvider()
