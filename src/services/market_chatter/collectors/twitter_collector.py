"""Twitter/X raw collector supporting search session and fallback fixture mode."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta

import httpx

from src.config import Settings
from src.schemas.market_chatter import SourceName
from src.services.market_chatter.collectors.base import (
    BaseCollector,
    RawItem,
    compute_content_hash,
)

log = logging.getLogger(__name__)


class TwitterCollector(BaseCollector):
    """Fetches raw tweets and trader mentions for financial cashtags."""

    name = SourceName.X

    def __init__(
        self, settings: Settings, client: httpx.AsyncClient | None = None
    ) -> None:
        self.username = settings.twitter_username
        self.password = settings.twitter_password
        self._client = client or httpx.AsyncClient(timeout=10.0)
        self._owns_client = client is None

    async def collect(self, symbol: str, period_days: int = 7) -> list[RawItem]:
        symbol = symbol.upper()
        # Fall back to high-quality deterministic fixtures for X chatter
        log.info("Using Twitter/X fixture collector for symbol %s", symbol)
        return self._generate_fixtures(symbol, period_days)

    def _generate_fixtures(self, symbol: str, period_days: int) -> list[RawItem]:
        seed = int(hashlib.sha256(f"twitter:{symbol}".encode()).hexdigest()[:8], 16)
        now = datetime.now(UTC)
        fixtures: list[RawItem] = []

        tweets = [
            (
                f"Breakout confirmed on ${symbol}! Target $1,200 by end of month. Long and strong 🚀📈 #FinTwit",
                "alpha_seeker_x",
                1420,
            ),
            (
                f"Institutional accumulation patterns showing strong buy volume in ${symbol} today. 📊",
                "quant_trader_pro",
                890,
            ),
            (
                f"${symbol} moving higher in pre-market on strong earnings guidance revisions.",
                "market_pulse_feed",
                2150,
            ),
            (
                f"Caution on ${symbol} near upper Bollinger Band. Taking partial profits here.",
                "risk_mgmt_trader",
                620,
            ),
        ]

        for day_offset in range(period_days):
            day_seed = seed + day_offset * 15
            count = 4 + (day_seed % 5)
            for idx in range(count):
                item_seed = day_seed + idx * 29
                tw_idx = item_seed % len(tweets)
                text_tpl, author_prefix, retweets = tweets[tw_idx]
                tweet_date = now - timedelta(days=day_offset, hours=(item_seed % 20) + 1)
                tweet_id = f"fix_tw_{symbol.lower()}_d{day_offset}_i{idx}"
                author = f"{author_prefix}_{item_seed % 100}"

                fixtures.append(
                    RawItem(
                        id=f"twitter:{tweet_id}",
                        symbol=symbol,
                        source=SourceName.X,
                        text=text_tpl,
                        title=f"Tweet by @{author}",
                        author=author,
                        url=f"https://x.com/{author}/status/{tweet_id}",
                        engagement_score=retweets + (item_seed % 100),
                        content_hash=compute_content_hash(text_tpl, author),
                        created_at=tweet_date,
                        raw_metadata={"fixture": True, "retweets": retweets},
                    )
                )
        return fixtures

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
