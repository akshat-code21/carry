"""Financial News raw collector supporting RSS feeds and fallback fixture mode."""

from __future__ import annotations

import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime

import httpx

from src.schemas.market_chatter import SourceName
from src.services.market_chatter.collectors.base import (
    BaseCollector,
    RawItem,
    compute_content_hash,
)

log = logging.getLogger(__name__)


class NewsCollector(BaseCollector):
    """Fetches raw financial news headlines and articles for tickers."""

    name = SourceName.NEWS

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=10.0)
        self._owns_client = client is None

    async def collect(self, symbol: str, period_days: int = 7) -> list[RawItem]:
        symbol = symbol.upper()
        rss_url = f"https://news.google.com/rss/search?q={symbol}+stock&hl=en-US&gl=US&ceid=US:en"

        try:
            resp = await self._client.get(
                rss_url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
            )
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                channel = root.find("channel")
                if channel is not None:
                    items: list[RawItem] = []
                    now = datetime.now(UTC)
                    cutoff = now - timedelta(days=period_days)

                    for item in channel.findall("item"):
                        title = item.findtext("title", "")
                        link = item.findtext("link", "")
                        pub_date_raw = item.findtext("pubDate", "")
                        source_elem = item.find("source")
                        publisher = (
                            source_elem.text if source_elem is not None else "Financial News"
                        )

                        if not title:
                            continue

                        try:
                            pub_dt = parsedate_to_datetime(pub_date_raw)
                            if pub_dt.tzinfo is None:
                                pub_dt = pub_dt.replace(tzinfo=UTC)
                        except Exception:
                            pub_dt = now

                        if pub_dt < cutoff:
                            continue

                        article_id = hashlib.sha256(link.encode("utf-8")).hexdigest()[:16]

                        items.append(
                            RawItem(
                                id=f"news:{article_id}",
                                symbol=symbol,
                                source=SourceName.NEWS,
                                text=title,
                                title=title,
                                author=publisher,
                                url=link,
                                engagement_score=10,
                                content_hash=compute_content_hash(title, publisher),
                                created_at=pub_dt,
                                raw_metadata={"publisher": publisher, "link": link},
                            )
                        )
                    if items:
                        return items
        except Exception as exc:
            log.warning("News RSS fetch failed for %s: %s", symbol, exc)

        log.info("Using News fixture generator for symbol %s", symbol)
        return self._generate_fixtures(symbol, period_days)

    def _generate_fixtures(self, symbol: str, period_days: int) -> list[RawItem]:
        seed = int(hashlib.sha256(f"news:{symbol}".encode()).hexdigest()[:8], 16)
        now = datetime.now(UTC)
        fixtures: list[RawItem] = []

        articles = [
            (
                f"{symbol} Reports Record Quarterly Revenue Driven by Enterprise Demand",
                "Reuters",
                "https://reuters.com/business/finance",
                85,
            ),
            (
                f"Analysts Raise Price Target on {symbol} Following New Strategic Partnership",
                "Bloomberg",
                "https://bloomberg.com/markets",
                92,
            ),
            (
                f"Market Wrap: {symbol} Leads Sector Gains Amid Broader Tech Rally",
                "Wall Street Journal",
                "https://wsj.com/markets",
                78,
            ),
            (
                f"Regulatory Review Initiated for {symbol}'s Latest Acquisition Bid",
                "CNBC",
                "https://cnbc.com/markets",
                64,
            ),
        ]

        for day_offset in range(period_days):
            day_seed = seed + day_offset * 11
            count = 2 + (day_seed % 4)
            for idx in range(count):
                item_seed = day_seed + idx * 19
                art_idx = item_seed % len(articles)
                title, publisher, url, engagement = articles[art_idx]
                pub_date = now - timedelta(days=day_offset, hours=(item_seed % 20) + 1)
                article_id = f"fix_news_{symbol.lower()}_d{day_offset}_i{idx}"

                fixtures.append(
                    RawItem(
                        id=f"news:{article_id}",
                        symbol=symbol,
                        source=SourceName.NEWS,
                        text=title,
                        title=title,
                        author=publisher,
                        url=url,
                        engagement_score=engagement + (item_seed % 20),
                        content_hash=compute_content_hash(title, publisher),
                        created_at=pub_date,
                        raw_metadata={"fixture": True, "publisher": publisher},
                    )
                )
        return fixtures

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
