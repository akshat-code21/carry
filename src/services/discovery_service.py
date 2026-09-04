"""New-video discovery - shared by WebSub push and RSS fallback poll."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.channel import Channel
from src.models.video import Video
from src.services.activity_service import ActivityService
from src.services.interfaces import YouTubeService
from src.services.websub_service import WebSubEntry

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Idempotent discovery of new channel videos.

    Does not run LLM analysis - only creates Video rows, emits activity, and
    returns video IDs that should be queued for auto-ingest.
    """

    def __init__(
        self,
        db: AsyncSession,
        youtube: YouTubeService | None = None,
    ) -> None:
        self.db = db
        self.youtube = youtube
        self.activity = ActivityService(db)

    async def handle_discovered_video(
        self,
        *,
        youtube_channel_id: str | None,
        youtube_video_id: str,
        title: str | None = None,
        published_at: str | None = None,
        channel_id: uuid.UUID | None = None,
        is_short_flag: bool = False,
        source: str = "websub",
    ) -> dict[str, Any]:
        """Ensure a video is known and queue-worthy.

        Returns a result dict:
          - status: ignored_unknown_channel | already_exists | skipped_short | discovered | error
          - video_id: str | None  (internal UUID when created/known and needs ingest)
          - enqueue: bool
        """
        channel = await self._resolve_channel(
            youtube_channel_id=youtube_channel_id,
            channel_id=channel_id,
        )
        if not channel:
            logger.info(
                "Ignoring discovered video %s - unknown channel %s",
                youtube_video_id,
                youtube_channel_id,
            )
            return {
                "status": "ignored_unknown_channel",
                "video_id": None,
                "enqueue": False,
                "youtube_video_id": youtube_video_id,
            }

        # Already known?
        existing = await self.db.execute(
            select(Video).where(Video.youtube_video_id == youtube_video_id)
        )
        video = existing.scalar_one_or_none()
        if video:
            channel.last_checked_at = datetime.now(UTC)
            # Update-only WebSub pushes: ignore fully done / in-flight videos.
            # Re-enqueue only if still mid auto-ingest (e.g. awaiting captions).
            enqueue = not video.processed and video.ingest_status not in (
                "processing",
                "completed",
                "failed",
            )
            return {
                "status": "already_exists",
                "video_id": str(video.id) if enqueue else None,
                "enqueue": enqueue,
                "youtube_video_id": youtube_video_id,
                "channel_id": str(channel.id),
                "title": video.title,
            }

        # Enrich metadata / Shorts filter via YouTube API when available
        meta_title = title or youtube_video_id
        meta_description = None
        meta_published = published_at
        meta_duration: int | None = None
        meta_thumbnail = None
        meta_views: int | None = None

        if is_short_flag:
            logger.info("Skipping Short on discovery (feed flag): %s (%s)", title, youtube_video_id)
            channel.last_checked_at = datetime.now(UTC)
            return {
                "status": "skipped_short",
                "video_id": None,
                "enqueue": False,
                "youtube_video_id": youtube_video_id,
            }

        if self.youtube is not None:
            try:
                meta = await self.youtube.get_video_info(youtube_video_id)
                meta_title = meta.title or meta_title
                meta_description = meta.description
                meta_published = meta.published_at or meta_published
                meta_duration = meta.duration_sec
                meta_thumbnail = meta.thumbnail_url
                meta_views = meta.view_count

                if self._is_short(meta_duration, meta_title, is_short_flag=is_short_flag):
                    logger.info(
                        "Skipping Short on discovery: %s (%s)", meta_title, youtube_video_id
                    )
                    channel.last_checked_at = datetime.now(UTC)
                    return {
                        "status": "skipped_short",
                        "video_id": None,
                        "enqueue": False,
                        "youtube_video_id": youtube_video_id,
                    }
            except Exception as e:
                logger.warning(
                    "get_video_info failed for %s during discovery (continuing with feed data): %s",
                    youtube_video_id,
                    e,
                )
                # Title-based short heuristic without duration
                if self._is_short(None, meta_title, is_short_flag=is_short_flag):
                    return {
                        "status": "skipped_short",
                        "video_id": None,
                        "enqueue": False,
                        "youtube_video_id": youtube_video_id,
                    }

        published_dt = self._parse_published(meta_published)

        # Idempotent insert (race between push + poll)
        video_uuid = uuid.uuid4()
        stmt = (
            pg_insert(Video)
            .values(
                id=video_uuid,
                channel_id=channel.id,
                youtube_video_id=youtube_video_id,
                title=meta_title,
                description=meta_description,
                published_at=published_dt,
                duration_sec=meta_duration,
                thumbnail_url=meta_thumbnail,
                view_count=meta_views,
                transcript_status="pending",
                processed=False,
                ingest_status="discovered",
                transcript_attempts=0,
            )
            .on_conflict_do_nothing(index_elements=["youtube_video_id"])
            .returning(Video.id)
        )
        result = await self.db.execute(stmt)
        inserted_id = result.scalar_one_or_none()

        if inserted_id is None:
            # Lost race - fetch existing
            existing = await self.db.execute(
                select(Video).where(Video.youtube_video_id == youtube_video_id)
            )
            video = existing.scalar_one()
            channel.last_checked_at = datetime.now(UTC)
            return {
                "status": "already_exists",
                "video_id": None,
                "enqueue": False,
                "youtube_video_id": youtube_video_id,
                "channel_id": str(channel.id),
                "title": video.title,
            }

        await self.db.flush()
        video_id = inserted_id

        await self.activity.emit(
            event_type="video_detected",
            channel_id=channel.id,
            video_id=video_id,
            youtube_video_id=youtube_video_id,
            title=meta_title,
            message=f"New video detected on {channel.title}: {meta_title}",
            payload={"source": source, "channel_title": channel.title},
        )

        channel.last_checked_at = datetime.now(UTC)
        await self.db.flush()

        logger.info(
            "Discovered new video %s (%s) on channel %s via %s",
            meta_title,
            youtube_video_id,
            channel.title,
            source,
        )
        return {
            "status": "discovered",
            "video_id": str(video_id),
            "enqueue": True,
            "youtube_video_id": youtube_video_id,
            "channel_id": str(channel.id),
            "title": meta_title,
        }

    async def handle_websub_entries(
        self, entries: list[WebSubEntry], source: str = "websub"
    ) -> list[dict[str, Any]]:
        """Process a batch of WebSub/RSS entries; return per-entry results."""
        results = []
        for entry in entries:
            result = await self.handle_discovered_video(
                youtube_channel_id=entry.youtube_channel_id or None,
                youtube_video_id=entry.youtube_video_id,
                title=entry.title,
                published_at=entry.published_at,
                is_short_flag=entry.is_short,
                source=source,
            )
            results.append(result)
        return results

    async def _resolve_channel(
        self,
        *,
        youtube_channel_id: str | None,
        channel_id: uuid.UUID | None,
    ) -> Channel | None:
        if channel_id is not None:
            result = await self.db.execute(select(Channel).where(Channel.id == channel_id))
            return result.scalar_one_or_none()

        if youtube_channel_id:
            result = await self.db.execute(
                select(Channel).where(Channel.youtube_channel_id == youtube_channel_id)
            )
            return result.scalar_one_or_none()

        return None

    @staticmethod
    def _is_short(duration_sec: int | None, title: str, is_short_flag: bool = False) -> bool:
        if is_short_flag:
            return True
        if duration_sec is not None and 0 < duration_sec <= 180:
            return True
        title_lower = (title or "").lower()
        return "#shorts" in title_lower or "#short" in title_lower

    @staticmethod
    def _parse_published(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
