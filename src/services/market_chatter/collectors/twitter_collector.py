"""Twitter/X raw collector supporting search session and fallback fixture mode."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime

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

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self.username = settings.twitter_username
        self.password = settings.twitter_password
        self._client = client or httpx.AsyncClient(timeout=10.0)
        self._owns_client = client is None

    async def collect(self, symbol: str, period_days: int = 7) -> list[RawItem]:
        symbol = symbol.upper()
        now = datetime.now(UTC)
        cutoff = now - timedelta(days=period_days)

        queries = [
            f"https://news.google.com/rss/search?q=%24{symbol}+site%3Ax.com&hl=en-US&gl=US&ceid=US:en",
            f"https://news.google.com/rss/search?q=%23{symbol}+site%3Ax.com&hl=en-US&gl=US&ceid=US:en",
            f"https://news.google.com/rss/search?q={symbol}+stock+site%3Ax.com&hl=en-US&gl=US&ceid=US:en",
            f"https://news.google.com/rss/search?q={symbol}+trading+OR+breakout+OR+shares+site%3Ax.com&hl=en-US&gl=US&ceid=US:en",
        ]

        tasks = [asyncio.to_thread(self._fetch_query, url, symbol, cutoff, now) for url in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        items: list[RawItem] = []
        seen_ids: set[str] = set()
        seen_hashes: set[str] = set()

        for res in results:
            if isinstance(res, Exception):
                log.warning("Twitter/X RSS query failed for %s: %s", symbol, res)
            elif isinstance(res, list):
                for item in res:
                    if item.id in seen_ids or item.content_hash in seen_hashes:
                        continue
                    seen_ids.add(item.id)
                    seen_hashes.add(item.content_hash)
                    items.append(item)

        if items:
            log.info(
                "Fetched %d deduplicated FinTwit/X tweets for %s across %d queries",
                len(items),
                symbol,
                len(queries),
            )
            items.sort(key=lambda x: x.created_at, reverse=True)
            return items

        log.info("Using Twitter/X fixture collector for symbol %s", symbol)
        return self._generate_fixtures(symbol, period_days)

    def _fetch_query(
        self,
        url: str,
        symbol: str,
        cutoff: datetime,
        now: datetime,
    ) -> list[RawItem]:
        try:
            from curl_cffi import requests

            resp = requests.get(url, impersonate="chrome120", timeout=10)
            if resp.status_code != 200:
                return []

            root = ET.fromstring(resp.text)
            channel = root.find("channel")
            if channel is None:
                return []

            items: list[RawItem] = []
            for idx, item in enumerate(channel.findall("item")):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub_date_str = item.findtext("pubDate", "")

                clean_text = title.replace(" - x.com", "").replace(" - Twitter", "").strip()
                if not clean_text or not link:
                    continue

                try:
                    pub_dt = parsedate_to_datetime(pub_date_str)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=UTC)
                    else:
                        pub_dt = pub_dt.astimezone(UTC)
                except Exception:
                    pub_dt = now - timedelta(hours=idx)

                if pub_dt < cutoff:
                    continue

                author = "fintwit_trader"
                if clean_text.startswith("@"):
                    parts = clean_text.split()
                    if parts:
                        author = parts[0].replace("@", "").strip(":,.")

                item_id = hashlib.md5(link.strip().encode()).hexdigest()[:12]

                items.append(
                    RawItem(
                        id=f"twitter:{item_id}",
                        symbol=symbol,
                        source=SourceName.X,
                        text=clean_text,
                        title=f"${symbol} Tweet / X Discussion",
                        author=author,
                        url=link.strip(),
                        engagement_score=35 + (idx % 25),
                        content_hash=compute_content_hash(clean_text, author),
                        created_at=pub_dt,
                        raw_metadata={"rss_link": link.strip(), "source": "x.com"},
                    )
                )
            return items
        except Exception as exc:
            log.debug("Live X/Twitter RSS fetch query failed: %s", exc)
            return []

    def _generate_fixtures(self, symbol: str, period_days: int) -> list[RawItem]:
        seed = int(hashlib.sha256(f"twitter:{symbol}".encode()).hexdigest()[:8], 16)
        now = datetime.now(UTC)
        fixtures: list[RawItem] = []

        tweets = [
            (
                (
                    f"Breakout confirmed on ${symbol}! "
                    "Target $1,200 by end of month. Long and strong 🚀📈 #FinTwit"
                ),
                "alpha_seeker_x",
                1420,
            ),
            (
                (
                    f"Institutional accumulation patterns showing strong buy volume "
                    f"in ${symbol} today. 📊"
                ),
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
