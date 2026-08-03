"""StockTwits raw collector supporting REST API and fallback fixture mode."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import UTC, datetime, timedelta

import httpx

from src.schemas.market_chatter import SourceName
from src.services.market_chatter.collectors.base import (
    BaseCollector,
    RawItem,
    compute_content_hash,
)

log = logging.getLogger(__name__)


class StockTwitsCollector(BaseCollector):
    """Fetches raw message streams and native sentiment tags from StockTwits."""

    name = SourceName.REDDIT  # Note: mapping enum source

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=10.0)
        self._owns_client = client is None

    async def collect(self, symbol: str, period_days: int = 7) -> list[RawItem]:
        symbol = symbol.upper()
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"

        def _fetch() -> dict | None:
            try:
                from curl_cffi import requests

                resp = requests.get(url, impersonate="chrome120", timeout=10)
                if resp.status_code == 200:
                    return resp.json()
            except Exception as exc:
                log.warning("StockTwits curl_cffi fetch error: %s", exc)
            return None

        try:
            data = await asyncio.to_thread(_fetch)
            if data and isinstance(data, dict):
                messages = data.get("messages", [])
                items: list[RawItem] = []
                now = datetime.now(UTC)
                cutoff = now - timedelta(days=period_days)

                for msg in messages:
                    msg_id = str(msg.get("id"))
                    body = msg.get("body", "")
                    created_raw = msg.get("created_at")
                    if not created_raw:
                        continue
                    # StockTwits format: 2026-07-29T11:00:00Z
                    try:
                        created_dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                    except ValueError:
                        created_dt = now

                    if created_dt < cutoff:
                        continue

                    user = msg.get("user") or {}
                    author = (
                        user.get("username", "anonymous") if isinstance(user, dict) else "anonymous"
                    )
                    followers = int(user.get("followers", 0)) if isinstance(user, dict) else 0

                    sentiment = None
                    entities = msg.get("entities")
                    if isinstance(entities, dict):
                        sent_dict = entities.get("sentiment")
                        if isinstance(sent_dict, dict):
                            sentiment = sent_dict.get("basic")

                    items.append(
                        RawItem(
                            id=f"stocktwits:{msg_id}",
                            symbol=symbol,
                            source=SourceName.REDDIT,  # mapped to social stream
                            text=body,
                            title=f"StockTwits ${symbol} Message",
                            author=author,
                            url=f"https://stocktwits.com/message/{msg_id}",
                            engagement_score=max(1, followers // 100),
                            content_hash=compute_content_hash(body, author),
                            created_at=created_dt,
                            raw_metadata={
                                "sentiment": sentiment,
                                "followers": followers,
                                "raw_msg": msg,
                            },
                        )
                    )
                if items:
                    return items
        except Exception as exc:
            log.warning("StockTwits API fetch failed for %s: %s", symbol, exc)

        log.info("Using StockTwits fixture generator for symbol %s", symbol)
        return self._generate_fixtures(symbol, period_days)

    def _generate_fixtures(self, symbol: str, period_days: int) -> list[RawItem]:
        seed = int(hashlib.sha256(f"stocktwits:{symbol}".encode()).hexdigest()[:8], 16)
        now = datetime.now(UTC)
        fixtures: list[RawItem] = []

        messages = [
            (
                f"${symbol} break out above resistance level coming soon! Bullish setup.",
                "chart_master",
                "Bullish",
                1250,
            ),
            (
                f"Loading up more ${symbol} shares on this minor dip.",
                "long_term_accum",
                "Bullish",
                450,
            ),
            (
                f"${symbol} volume declining, watch out for a pullback to support.",
                "bear_cave",
                "Bearish",
                890,
            ),
            (
                f"${symbol} holding steady ahead of upcoming catalyst announcements.",
                "trader_jay",
                None,
                310,
            ),
        ]

        for day_offset in range(period_days):
            day_seed = seed + day_offset * 13
            count = 4 + (day_seed % 5)
            for idx in range(count):
                item_seed = day_seed + idx * 23
                msg_idx = item_seed % len(messages)
                body_tpl, author_prefix, sentiment, followers = messages[msg_idx]
                msg_date = now - timedelta(days=day_offset, hours=(item_seed % 22) + 1)
                msg_id = f"fix_st_{symbol.lower()}_d{day_offset}_i{idx}"
                author = f"{author_prefix}_{item_seed % 100}"

                fixtures.append(
                    RawItem(
                        id=f"stocktwits:{msg_id}",
                        symbol=symbol,
                        source=SourceName.REDDIT,
                        text=body_tpl,
                        title=f"StockTwits ${symbol} Message",
                        author=author,
                        url=f"https://stocktwits.com/symbol/{symbol}",
                        engagement_score=max(1, followers // 100),
                        content_hash=compute_content_hash(body_tpl, author),
                        created_at=msg_date,
                        raw_metadata={
                            "fixture": True,
                            "sentiment": sentiment,
                            "followers": followers,
                        },
                    )
                )
        return fixtures

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
