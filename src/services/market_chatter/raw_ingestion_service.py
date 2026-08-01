"""Orchestrates raw social, news, and trader content ingestion across platforms."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.models.raw_content import RawContent
from src.schemas.market_chatter import SourceName
from src.services.market_chatter.collectors import (
    BaseCollector,
    NewsCollector,
    RawItem,
    RedditCollector,
    StockTwitsCollector,
    TwitterCollector,
)

log = logging.getLogger(__name__)


class RawIngestionService:
    """Runs collectors concurrently and persists deduplicated RawContent records."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.collectors: list[BaseCollector] = [
            RedditCollector(settings),
            StockTwitsCollector(),
            NewsCollector(),
            TwitterCollector(settings),
        ]

    async def ingest_symbol(
        self, session: AsyncSession, symbol: str, period_days: int = 30
    ) -> dict[str, Any]:
        symbol = symbol.upper()
        log.info("Starting raw ingestion for symbol %s over %d days", symbol, period_days)

        results = await asyncio.gather(
            *[c.collect(symbol, period_days) for c in self.collectors],
            return_exceptions=True,
        )

        all_items: list[RawItem] = []
        for collector, res in zip(self.collectors, results):
            if isinstance(res, Exception):
                log.error("Collector %s failed for %s: %s", collector.name, symbol, res)
            elif isinstance(res, list):
                all_items.extend(res)

        if not all_items:
            log.warning("No raw items collected for symbol %s", symbol)
            return {"symbol": symbol, "total_collected": 0, "inserted": 0, "by_source": {}}

        # Fetch existing hashes/IDs to perform exact deduplication
        hashes = {item.content_hash for item in all_items}
        stmt = select(RawContent.content_hash).where(
            RawContent.symbol == symbol,
            RawContent.content_hash.in_(hashes),
        )
        existing_res = await session.execute(stmt)
        existing_hashes = set(existing_res.scalars().all())

        new_records: list[RawContent] = []
        by_source: dict[str, int] = {}

        for item in all_items:
            source_key = item.source.value if hasattr(item.source, "value") else str(item.source)
            by_source[source_key] = by_source.get(source_key, 0) + 1

            if item.content_hash in existing_hashes:
                continue

            existing_hashes.add(item.content_hash)
            new_records.append(
                RawContent(
                    id=item.id,
                    symbol=item.symbol,
                    source=source_key,
                    text=item.text,
                    title=item.title,
                    author=item.author,
                    url=item.url,
                    engagement_score=item.engagement_score,
                    content_hash=item.content_hash,
                    created_at=item.created_at,
                    fetched_at=item.fetched_at,
                    raw_metadata=item.raw_metadata,
                )
            )

        if new_records:
            session.add_all(new_records)
            await session.commit()
            log.info("Persisted %d new raw records for symbol %s", len(new_records), symbol)

        return {
            "symbol": symbol,
            "total_collected": len(all_items),
            "inserted": len(new_records),
            "by_source": by_source,
        }

    async def close(self) -> None:
        for collector in self.collectors:
            await collector.close()
