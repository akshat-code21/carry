"""Base collector protocols and Pydantic schemas for Raw Ingestion."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from src.schemas.market_chatter import SourceName


def compute_content_hash(text: str, author: str | None = None) -> str:
    """Derive deterministic SHA-256 fingerprint for content deduplication."""
    payload = f"{(author or '').strip().lower()}:{' '.join(text.split())}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class RawItem(BaseModel):
    """Canonical raw social, news, or trader content record."""

    id: str
    symbol: str
    source: SourceName
    text: str
    title: str | None = None
    author: str | None = None
    url: str | None = None
    engagement_score: int = 0
    content_hash: str
    created_at: datetime
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class BaseCollector(ABC):
    """Abstract interface for all raw data source connectors."""

    name: SourceName

    @abstractmethod
    async def collect(self, symbol: str, period_days: int = 7) -> list[RawItem]:
        """Fetch raw social posts or articles for a symbol over a period."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Cleanup HTTP clients or connections."""
        ...
