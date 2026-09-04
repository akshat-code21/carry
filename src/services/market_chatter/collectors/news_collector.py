"""Financial News raw collector supporting RSS feeds and fallback fixture mode."""

from __future__ import annotations

import asyncio
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
        now = datetime.now(UTC)
        cutoff = now - timedelta(days=period_days)

        feed_configs = [
            (
                f"https://news.google.com/rss/search?q={symbol}+stock&hl=en-US&gl=US&ceid=US:en",
                "Financial News",
            ),
            (
                f"https://news.google.com/rss/search?q={symbol}+shares+OR+earnings+OR+revenue+OR+rating&hl=en-US&gl=US&ceid=US:en",
                "Financial News",
            ),
            (
                f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US",
                "Yahoo Finance",
            ),
            (
                f"https://seekingalpha.com/api/sa/combined/{symbol}.xml",
                "Seeking Alpha",
            ),
        ]

        tasks = [
            self._fetch_rss_feed(url, default_publisher, symbol, cutoff, now)
            for url, default_publisher in feed_configs
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        items: list[RawItem] = []
        seen_ids: set[str] = set()
        seen_hashes: set[str] = set()

        for res in results:
            if isinstance(res, Exception):
                log.warning("News RSS feed fetch error for %s: %s", symbol, res)
            elif isinstance(res, list):
                for item in res:
                    if item.id in seen_ids or item.content_hash in seen_hashes:
                        continue
                    seen_ids.add(item.id)
                    seen_hashes.add(item.content_hash)
                    items.append(item)

        if items:
            log.info(
                "Fetched %d deduplicated news articles for %s across %d feeds",
                len(items),
                symbol,
                len(feed_configs),
            )
            # Sort newest first
            items.sort(key=lambda x: x.created_at, reverse=True)
            return items

        log.info("Using News fixture generator for symbol %s", symbol)
        return self._generate_fixtures(symbol, period_days)

    async def _fetch_rss_feed(
        self,
        url: str,
        default_publisher: str,
        symbol: str,
        cutoff: datetime,
        now: datetime,
    ) -> list[RawItem]:
        try:
            resp = await self._client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": ("application/rss+xml, application/xml, text/xml, */*"),
                },
            )
            if resp.status_code != 200:
                return []

            root = ET.fromstring(resp.text)
            channel = root.find("channel")
            if channel is None:
                return []

            feed_items: list[RawItem] = []
            for item in channel.findall("item"):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub_date_raw = item.findtext("pubDate", "")
                source_elem = item.find("source")
                publisher = (
                    source_elem.text.strip()
                    if source_elem is not None and source_elem.text
                    else default_publisher
                )

                if not title or not link:
                    continue

                clean_title = title.strip()

                try:
                    pub_dt = parsedate_to_datetime(pub_date_raw)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=UTC)
                    else:
                        pub_dt = pub_dt.astimezone(UTC)
                except Exception:
                    pub_dt = now

                if pub_dt < cutoff:
                    continue

                article_id = hashlib.sha256(link.strip().encode("utf-8")).hexdigest()[:16]

                feed_items.append(
                    RawItem(
                        id=f"news:{article_id}",
                        symbol=symbol,
                        source=SourceName.NEWS,
                        text=clean_title,
                        title=clean_title,
                        author=publisher,
                        url=link.strip(),
                        engagement_score=15,
                        content_hash=compute_content_hash(clean_title, publisher),
                        created_at=pub_dt,
                        raw_metadata={"publisher": publisher, "link": link.strip()},
                    )
                )
            return feed_items
        except Exception as exc:
            log.debug("Failed parsing RSS from %s for %s: %s", url, symbol, exc)
            return []

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
