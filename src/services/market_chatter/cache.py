"""Best-effort Redis JSON cache.

PostgreSQL remains the durable source of truth.  If Redis is unavailable the
application continues without caching.
"""

from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis


class JsonCache:
    """Best-effort Redis cache. PostgreSQL remains the durable source of truth."""

    def __init__(self, redis: Redis | None = None) -> None:
        self._redis = redis

    @classmethod
    async def connect(cls, url: str | None) -> JsonCache:
        if not url:
            return cls()
        client = Redis.from_url(url, encoding="utf-8", decode_responses=True)
        try:
            await client.ping()
        except Exception:
            await client.aclose()
            return cls()
        return cls(client)

    async def get(self, key: str) -> dict[str, Any] | None:
        if not self._redis:
            return None
        try:
            value = await self._redis.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None

    async def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        if not self._redis:
            return
        try:
            await self._redis.set(key, json.dumps(value, default=str), ex=ttl_seconds)
        except Exception:
            return

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()
