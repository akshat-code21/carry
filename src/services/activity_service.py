"""In-app activity feed service."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.activity_event import ActivityEvent

logger = logging.getLogger(__name__)


class ActivityService:
    """Create and query activity events for the in-app notification feed."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def emit(
        self,
        *,
        event_type: str,
        channel_id: uuid.UUID,
        youtube_video_id: str,
        title: str,
        message: str,
        video_id: uuid.UUID | None = None,
        payload: dict[str, Any] | None = None,
    ) -> ActivityEvent | None:
        """Insert an activity event if (event_type, youtube_video_id) is new.

        Returns the event on insert, or None if it already existed (idempotent).
        """
        stmt = (
            pg_insert(ActivityEvent)
            .values(
                id=uuid.uuid4(),
                event_type=event_type,
                channel_id=channel_id,
                video_id=video_id,
                youtube_video_id=youtube_video_id,
                title=title,
                message=message,
                payload=payload,
            )
            .on_conflict_do_nothing(
                constraint="uq_activity_event_type_youtube_video"
            )
            .returning(ActivityEvent)
        )
        result = await self.db.execute(stmt)
        event = result.scalar_one_or_none()
        if event:
            logger.info(
                "Activity emitted: %s for video %s (%s)",
                event_type,
                youtube_video_id,
                title,
            )
        else:
            logger.debug(
                "Activity already exists: %s / %s", event_type, youtube_video_id
            )
        return event

    async def list_events(
        self,
        *,
        limit: int = 50,
        unread_only: bool = False,
        offset: int = 0,
    ) -> list[ActivityEvent]:
        q = select(ActivityEvent).order_by(ActivityEvent.created_at.desc())
        if unread_only:
            q = q.where(ActivityEvent.read_at.is_(None))
        q = q.offset(offset).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def unread_count(self) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(ActivityEvent)
            .where(ActivityEvent.read_at.is_(None))
        )
        return int(result.scalar_one() or 0)

    async def mark_read(self, event_id: uuid.UUID) -> ActivityEvent | None:
        result = await self.db.execute(
            select(ActivityEvent).where(ActivityEvent.id == event_id)
        )
        event = result.scalar_one_or_none()
        if not event:
            return None
        if event.read_at is None:
            event.read_at = datetime.now(UTC)
            await self.db.flush()
        return event

    async def mark_all_read(self) -> int:
        result = await self.db.execute(
            update(ActivityEvent)
            .where(ActivityEvent.read_at.is_(None))
            .values(read_at=datetime.now(UTC))
        )
        await self.db.flush()
        return int(result.rowcount or 0)
