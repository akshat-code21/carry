"""Step 1: YouTube Data Ingestion.

Fetches channel metadata, video list, and transcripts from YouTube.
Stores everything in the database.
"""

import json
import logging
import uuid as uuid_mod
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.models.channel import Channel
from src.models.transcript_segment import TranscriptSegment
from src.models.video import Video
from src.services.interfaces import TranscriptSource, YouTubeService

logger = logging.getLogger(__name__)
settings = get_settings()

CHANNEL_CLASSIFICATION_PROMPT = """Classify this YouTube channel as either \
"individual" or "institutional".

- "institutional": Financial institutions, banks, brokerages, research firms, hedge funds, \
asset managers, financial news networks, or any channel representing a company/organization \
rather than a person. Examples: Fundstrat, Morgan Stanley, Goldman Sachs, JP Morgan, \
BlackRock, Bloomberg, CNBC, Barclays, UBS, Deutsche Bank, BofA Securities, Citi, \
Wells Fargo, Jefferies.
- "individual": Personal channels run by individual traders, analysts, influencers, or \
content creators. The channel is clearly associated with one person or a small team creating \
personal content. Examples: ProfGMarkets, Meet Kevin, Stock Moe, Andrei Jikh, Graham Stephan.

Channel Title: "{title}"
Channel Description: "{description}"

Return ONLY valid JSON: {{"channel_type": "individual" or "institutional"}}"""


class IngestionPipeline:
    """Pipeline step 1: Fetch and store YouTube data."""

    def __init__(
        self,
        db: AsyncSession,
        youtube_service: YouTubeService,
        transcript_source: TranscriptSource,
    ) -> None:
        self.db = db
        self.youtube = youtube_service
        self.transcript_source = transcript_source

    async def ingest_channel(self, youtube_channel_id: str, max_videos: int = 20) -> Channel:
        """Ingest a YouTube channel — fetch metadata and store it.

        Returns the Channel ORM object (created or existing).
        """
        # Check if channel already exists
        result = await self.db.execute(
            select(Channel).where(Channel.youtube_channel_id == youtube_channel_id)
        )
        channel = result.scalar_one_or_none()

        if channel:
            logger.info(f"Channel already exists: {channel.title}")
            return channel

        # Fetch channel metadata from YouTube
        channel_meta = await self.youtube.get_channel_info(youtube_channel_id)

        # Classify channel type via lightweight LLM call
        channel_type = await self._classify_channel_type(
            channel_meta.title, channel_meta.description or ""
        )

        channel = Channel(
            youtube_channel_id=youtube_channel_id,
            title=channel_meta.title,
            description=channel_meta.description,
            thumbnail_url=channel_meta.thumbnail_url,
            channel_type=channel_type,
        )
        self.db.add(channel)
        await self.db.flush()

        logger.info(f"Ingested channel: {channel.title} ({channel.id}) [type={channel_type}]")
        return channel

    async def _classify_channel_type(self, title: str, description: str) -> str:
        """Classify a channel as 'individual' or 'institutional' using a lightweight LLM call.

        Falls back to 'individual' if classification fails.
        """
        try:
            if not settings.openai_api_key:
                logger.warning("No OpenAI API key — defaulting channel_type to 'individual'")
                return "individual"

            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)

            # Truncate description to avoid token waste
            desc_truncated = description[:500] if description else ""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "user",
                        "content": CHANNEL_CLASSIFICATION_PROMPT.format(
                            title=title, description=desc_truncated
                        ),
                    },
                ],
                temperature=0.0,
                max_completion_tokens=50,
            )

            content = response.choices[0].message.content
            data = json.loads(content)
            channel_type = data.get("channel_type", "individual")

            if channel_type not in ("individual", "institutional"):
                logger.warning(
                    f"Unexpected channel_type '{channel_type}' from LLM, defaulting to 'individual'"
                )
                return "individual"

            logger.info(f"Channel '{title}' classified as: {channel_type}")
            return channel_type

        except Exception as e:
            logger.warning(
                f"Channel classification failed for '{title}', defaulting to 'individual': {e}"
            )
            return "individual"

    async def backfill_videos(self, channel: Channel, max_videos: int = 20) -> list[Video]:
        """Backfill videos for a channel — fetch metadata and store them.

        Skips videos that already exist in the database.
        """
        video_metas = await self.youtube.list_channel_videos(
            channel.youtube_channel_id, max_results=max_videos
        )

        created_videos: list[Video] = []

        for meta in video_metas:
            # Skip if video is a Short (duration <= 60s or title contains shorts tag)
            if (
                (meta.duration_sec is not None and meta.duration_sec <= 60)
                or "#shorts" in meta.title.lower()
                or "#short" in meta.title.lower()
            ):
                logger.info(
                    f"Skipping Short video during backfill: '{meta.title}' ({meta.video_id})"
                )
                continue

            # Check if video already exists
            existing = await self.db.execute(
                select(Video).where(Video.youtube_video_id == meta.video_id)
            )
            if existing.scalar_one_or_none():
                logger.debug(f"Video already exists: {meta.title}")
                continue

            # Parse published_at
            published_at = None
            if meta.published_at:
                try:
                    published_at = datetime.fromisoformat(meta.published_at.replace("Z", "+00:00"))
                except ValueError:
                    pass

            video = Video(
                channel_id=channel.id,
                youtube_video_id=meta.video_id,
                title=meta.title,
                description=meta.description,
                published_at=published_at,
                duration_sec=meta.duration_sec,
                thumbnail_url=meta.thumbnail_url,
                view_count=meta.view_count,
                transcript_status="pending",
                processed=False,
            )
            self.db.add(video)
            created_videos.append(video)

        await self.db.flush()
        logger.info(f"Backfilled {len(created_videos)} new videos for {channel.title}")
        return created_videos

    async def ingest_single_video(self, channel_id: uuid_mod.UUID, youtube_video_id: str) -> Video:
        """Ingest a single video for a channel by YouTube Video ID.

        If video already exists, fetches transcript if needed and returns Video.
        Otherwise fetches metadata & transcript, stores in DB, and returns Video.
        """
        # Check if video already exists
        existing = await self.db.execute(
            select(Video).where(Video.youtube_video_id == youtube_video_id)
        )
        video = existing.scalar_one_or_none()

        if video:
            logger.info(f"Video already exists in database: {video.title} ({video.id})")
            if video.transcript_status == "pending":
                await self.fetch_transcript(video)
            return video

        # Fetch video metadata from YouTube
        meta = await self.youtube.get_video_info(youtube_video_id)

        published_at = None
        if meta.published_at:
            try:
                published_at = datetime.fromisoformat(meta.published_at.replace("Z", "+00:00"))
            except ValueError:
                pass

        video = Video(
            channel_id=channel_id,
            youtube_video_id=youtube_video_id,
            title=meta.title,
            description=meta.description,
            published_at=published_at,
            duration_sec=meta.duration_sec,
            thumbnail_url=meta.thumbnail_url,
            view_count=meta.view_count,
            transcript_status="pending",
            processed=False,
        )
        self.db.add(video)
        await self.db.flush()

        # Fetch transcript
        await self.fetch_transcript(video)

        return video

    async def fetch_transcript(self, video: Video) -> list[TranscriptSegment]:
        """Fetch and store transcript segments for a video.

        Updates the video's transcript_status accordingly.
        """
        try:
            # Fetch transcript via the pluggable source
            raw_segments = await self.transcript_source.fetch_transcript(video.youtube_video_id)

            # Store segments in the database
            db_segments: list[TranscriptSegment] = []
            for seg in raw_segments:
                db_seg = TranscriptSegment(
                    video_id=video.id,
                    start_sec=seg.start_sec,
                    end_sec=seg.end_sec,
                    text=seg.text,
                )
                self.db.add(db_seg)
                db_segments.append(db_seg)

            video.transcript_status = "fetched"
            await self.db.flush()

            logger.info(f"Fetched {len(db_segments)} transcript segments for: {video.title}")
            return db_segments

        except NotImplementedError:
            video.transcript_status = "failed"
            await self.db.flush()
            logger.warning(f"Transcript fetch failed (no fallback) for: {video.title}")
            raise

        except Exception as e:
            video.transcript_status = "failed"
            await self.db.flush()
            logger.error(f"Transcript fetch failed for {video.title}: {e}")
            raise

    async def ingest_and_backfill(self, youtube_channel_id: str, max_videos: int = 20) -> dict:
        """Full ingestion pipeline: channel → videos → transcripts.

        Returns a summary dict of what was ingested.
        """
        # Step 1a: Ingest channel
        channel = await self.ingest_channel(youtube_channel_id)

        # Step 1b: Backfill videos
        videos = await self.backfill_videos(channel, max_videos)

        # Step 1c: Fetch transcripts for all new videos
        transcript_results = {"fetched": 0, "failed": 0}

        # Also process existing pending videos
        pending_result = await self.db.execute(
            select(Video).where(
                Video.channel_id == channel.id,
                Video.transcript_status == "pending",
            )
        )
        pending_videos = list(pending_result.scalars().all())

        for video in pending_videos:
            try:
                await self.fetch_transcript(video)
                transcript_results["fetched"] += 1
            except Exception as e:
                transcript_results["failed"] += 1
                logger.warning(f"Skipping transcript for {video.title}: {e}")

        await self.db.commit()

        return {
            "channel": {
                "id": str(channel.id),
                "title": channel.title,
            },
            "videos_created": len(videos),
            "transcripts": transcript_results,
        }
