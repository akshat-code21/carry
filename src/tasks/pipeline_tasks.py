"""Celery tasks for the data pipeline.

Each task wraps a pipeline step and runs it asynchronously via Celery.
Tasks use asyncio.run() to bridge Celery's sync worker with async pipeline code.
"""

import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta

from src.tasks import celery_app

logger = logging.getLogger(__name__)


def _get_db_session():
    """Create a new async session for use within a Celery task."""
    from src.database import async_session_factory

    return async_session_factory()


def _get_services():
    """Instantiate all services needed by the pipeline."""
    from src.config import get_settings
    from src.services.embedding_service import OpenAIEmbeddingService
    from src.services.finbert_service import FinBertService
    from src.services.llm_service import AnthropicLLMService, OpenAILLMService
    from src.services.market_data_service import YFinanceMarketDataService
    from src.services.youtube_service import YouTubeAPIService, YouTubeTranscriptFetcher

    settings = get_settings()

    # Use Anthropic if key is set, otherwise default to OpenAI
    if settings.anthropic_api_key:
        llm_provider = AnthropicLLMService()
    else:
        llm_provider = OpenAILLMService()

    return {
        "youtube": YouTubeAPIService(),
        "transcript": YouTubeTranscriptFetcher(),
        "llm": llm_provider,
        "embedding": OpenAIEmbeddingService(),
        "market_data": YFinanceMarketDataService(),
        "finbert": FinBertService(),
    }


async def _run_and_cleanup(coro):
    """Run an async coroutine and guarantee engine disposal afterwards.

    This prevents asyncpg connection loop mismatch errors during repeated
    asyncio.run() invocations within the same Celery worker process.
    """
    try:
        return await coro
    finally:
        from src.database import engine

        await engine.dispose()


@celery_app.task(bind=True, name="pipeline.process_video")
def process_video_task(self, video_id: str) -> dict:
    """Run the full pipeline for a single video.

    Steps: analysis → theme mapping → embeddings → market tracking
    (Assumes transcript already fetched during ingestion.)
    """

    async def _run():
        services = _get_services()
        async with _get_db_session() as db:
            from sqlalchemy import select

            from src.models.video import Video
            from src.pipeline.analysis import AnalysisPipeline
            from src.pipeline.embeddings import EmbeddingPipeline
            from src.pipeline.market_tracking import MarketTrackingPipeline
            from src.pipeline.theme_mapping import ThemeMappingPipeline
            from src.services.activity_service import ActivityService
            from src.services.aggregation_service import AggregationService
            from src.services.theme_service import ThemeService

            vid = uuid.UUID(video_id)
            result = await db.execute(select(Video).where(Video.id == vid))
            video = result.scalar_one_or_none()
            if not video:
                return {"error": "video_not_found", "video_id": video_id}

            video.ingest_status = "processing"
            await db.flush()

            results: dict = {}
            try:
                # Step 2: LLM Analysis
                theme_service = ThemeService(db)
                analysis = AnalysisPipeline(db, services["llm"], theme_service, services["finbert"])
                results["analysis"] = await analysis.analyze_video(vid)

                # Step 3: Theme→Ticker Mapping
                aggregation_service = AggregationService(db)
                theme_mapping = ThemeMappingPipeline(
                    db, services["llm"], theme_service, aggregation_service
                )
                results["theme_mapping"] = await theme_mapping.enrich_video_themes(vid)

                # Step 4: Embeddings
                embedding = EmbeddingPipeline(db, services["embedding"])
                results["embeddings"] = await embedding.embed_video_segments(vid)

                # Step 5: Market Tracking
                market = MarketTrackingPipeline(db, services["market_data"])
                results["market_tracking"] = await market.track_video_predictions(vid)

                video.ingest_status = "completed"
                await db.flush()

                activity = ActivityService(db)
                await activity.emit(
                    event_type="video_processed",
                    channel_id=video.channel_id,
                    video_id=video.id,
                    youtube_video_id=video.youtube_video_id,
                    title=video.title,
                    message=f"Video ready: {video.title}",
                    payload={"video_id": str(video.id)},
                )

                await db.commit()
                return results
            except Exception as e:
                logger.exception("process_video_task failed for %s", video_id)
                video.ingest_status = "failed"
                activity = ActivityService(db)
                await activity.emit(
                    event_type="video_failed",
                    channel_id=video.channel_id,
                    video_id=video.id,
                    youtube_video_id=video.youtube_video_id,
                    title=video.title,
                    message=f"Processing failed for {video.title}: {e}",
                    payload={"error": str(e), "stage": "process_video"},
                )
                await db.commit()
                raise

    return asyncio.run(_run_and_cleanup(_run()))


@celery_app.task(bind=True, name="pipeline.backfill_channel")
def backfill_channel_task(self, youtube_channel_id: str, max_videos: int = 20) -> dict:
    """Run full ingestion + processing pipeline for a channel.

    Steps: ingest channel → backfill videos → fetch transcripts → process each video
    """

    async def _run():
        services = _get_services()
        channel_db_id: str | None = None

        async with _get_db_session() as db:
            from src.pipeline.ingestion import IngestionPipeline

            # Step 1: Ingestion
            ingestion = IngestionPipeline(db, services["youtube"], services["transcript"])
            ingestion_result = await ingestion.ingest_and_backfill(youtube_channel_id, max_videos)
            await db.commit()
            channel_db_id = ingestion_result.get("channel", {}).get("id")

            # Subscribe new/existing channel to WebSub when public URL is set
            if channel_db_id:
                subscribe_channel_websub_task.delay(channel_db_id)

        # Process only unprocessed videos for THIS channel (not global)
        from sqlalchemy import select

        from src.models.video import Video

        async with _get_db_session() as db:
            q = select(Video).where(
                Video.transcript_status == "fetched",
                Video.processed.is_(False),
            )
            if channel_db_id:
                q = q.where(Video.channel_id == uuid.UUID(channel_db_id))
            result = await db.execute(q)
            unprocessed = result.scalars().all()
            video_ids = [str(v.id) for v in unprocessed]

        for vid_id in video_ids:
            process_video_task.delay(vid_id)

        return {
            "ingestion": ingestion_result,
            "videos_queued_for_processing": len(video_ids),
        }

    return asyncio.run(_run_and_cleanup(_run()))


@celery_app.task(bind=True, name="pipeline.ingest_single_video")
def ingest_single_video_task(self, channel_id: str, youtube_video_id: str) -> dict:
    """Ingest a single video for a channel, fetch transcript, and queue for processing."""

    async def _run():
        services = _get_services()
        async with _get_db_session() as db:
            from src.pipeline.ingestion import IngestionPipeline

            ingestion = IngestionPipeline(db, services["youtube"], services["transcript"])
            c_uuid = uuid.UUID(channel_id)
            video = await ingestion.ingest_single_video(c_uuid, youtube_video_id)
            if video.transcript_status == "fetched":
                video.ingest_status = "ready_for_analysis"
            else:
                video.ingest_status = "failed"
                logger.warning(
                    "Transcript not available for %s (status: %s), skipping processing",
                    youtube_video_id,
                    video.transcript_status,
                )
            await db.commit()
            video_id_str = str(video.id)
            already_processed = video.processed
            transcript_ready = video.transcript_status == "fetched"

        if not already_processed and transcript_ready:
            process_video_task.delay(video_id_str)

        return {
            "video_id": video_id_str,
            "youtube_video_id": youtube_video_id,
            "status": "queued_for_processing" if not already_processed else "already_processed",
        }

    return asyncio.run(_run_and_cleanup(_run()))


@celery_app.task(bind=True, name="pipeline.auto_ingest_video")
def auto_ingest_video_task(self, video_id: str) -> dict:
    """Auto-ingest path: fetch transcript with retries, then queue process_video.

    Retry schedule from settings.transcript_retry_delays (minutes).
    """

    async def _run():
        from sqlalchemy import select

        from src.config import get_settings
        from src.models.video import Video
        from src.pipeline.ingestion import IngestionPipeline
        from src.services.activity_service import ActivityService

        settings = get_settings()
        delays = settings.transcript_retry_delays
        services = _get_services()
        vid = uuid.UUID(video_id)

        async with _get_db_session() as db:
            result = await db.execute(select(Video).where(Video.id == vid))
            video = result.scalar_one_or_none()
            if not video:
                return {"status": "not_found", "video_id": video_id}

            if video.processed or video.ingest_status == "completed":
                return {"status": "already_processed", "video_id": video_id}

            if video.ingest_status == "processing":
                return {"status": "already_processing", "video_id": video_id}

            # Transcript already available
            if video.transcript_status == "fetched":
                video.ingest_status = "ready_for_analysis"
                await db.commit()
                process_video_task.delay(video_id)
                return {"status": "queued_for_processing", "video_id": video_id}

            video.ingest_status = "awaiting_transcript"
            video.transcript_attempts = (video.transcript_attempts or 0) + 1
            attempt = video.transcript_attempts
            await db.flush()

            ingestion = IngestionPipeline(db, services["youtube"], services["transcript"])
            try:
                await ingestion.fetch_transcript(video)
                video.ingest_status = "ready_for_analysis"
                await db.commit()
                process_video_task.delay(video_id)
                return {
                    "status": "queued_for_processing",
                    "video_id": video_id,
                    "attempt": attempt,
                }
            except Exception as e:
                logger.warning(
                    "Transcript fetch attempt %s failed for %s: %s",
                    attempt,
                    video.youtube_video_id,
                    e,
                )
                # attempt is 1-based. After attempt k fails, schedule delays[k]
                # if present (delays[0] is the pre-first-attempt delay, usually 0).
                if attempt < len(delays):
                    delay_minutes = delays[attempt]
                    video.transcript_status = "pending"
                    video.ingest_status = "awaiting_transcript"
                    await db.commit()
                    countdown = max(0, delay_minutes * 60)
                    logger.info(
                        "Scheduling transcript retry for %s in %s min (attempt %s)",
                        video.youtube_video_id,
                        delay_minutes,
                        attempt + 1,
                    )
                    auto_ingest_video_task.apply_async(args=[video_id], countdown=countdown)
                    return {
                        "status": "retry_scheduled",
                        "video_id": video_id,
                        "attempt": attempt,
                        "countdown_sec": countdown,
                        "error": str(e),
                    }

                video.transcript_status = "failed"
                video.ingest_status = "failed"
                activity = ActivityService(db)
                await activity.emit(
                    event_type="video_failed",
                    channel_id=video.channel_id,
                    video_id=video.id,
                    youtube_video_id=video.youtube_video_id,
                    title=video.title,
                    message=(f"Transcript unavailable after {attempt} attempts for {video.title}"),
                    payload={
                        "error": str(e),
                        "stage": "transcript",
                        "attempts": attempt,
                    },
                )
                await db.commit()
                return {
                    "status": "failed",
                    "video_id": video_id,
                    "attempt": attempt,
                    "error": str(e),
                }

    return asyncio.run(_run_and_cleanup(_run()))


@celery_app.task(bind=True, name="pipeline.handle_websub_notification")
def handle_websub_notification_task(
    self,
    body: str,
    enqueue_ingest: bool = True,
    source: str = "websub",
) -> dict:
    """Parse a WebSub Atom body and run discovery for each entry.

    Args:
        body: Raw Atom XML from the hub (or a simulated payload).
        enqueue_ingest: When False, only discovery + video_detected activity
            (dry-run of the "new upload" path without transcript/LLM).
        source: Stored on activity payload (websub | simulate | rss_fallback).
    """

    async def _run():
        services = _get_services()
        from src.services.discovery_service import DiscoveryService
        from src.services.websub_service import WebSubService

        websub = WebSubService()
        entries = websub.parse_atom_notification(body)
        if not entries:
            return {"status": "empty", "discovered": 0, "enqueued": 0}

        enqueued = 0
        results = []
        async with _get_db_session() as db:
            discovery = DiscoveryService(db, services["youtube"])
            results = await discovery.handle_websub_entries(entries, source=source)
            await db.commit()

        if enqueue_ingest:
            for r in results:
                if r.get("enqueue") and r.get("video_id"):
                    auto_ingest_video_task.delay(r["video_id"])
                    enqueued += 1

        return {
            "status": "ok",
            "entries": len(entries),
            "results": results,
            "enqueued": enqueued,
            "enqueue_ingest": enqueue_ingest,
            "source": source,
        }

    return asyncio.run(_run_and_cleanup(_run()))


@celery_app.task(bind=True, name="pipeline.subscribe_channel_websub")
def subscribe_channel_websub_task(self, channel_id: str) -> dict:
    """Subscribe a channel's Atom feed to the Google WebSub hub."""

    async def _run():
        from sqlalchemy import select

        from src.config import get_settings
        from src.models.channel import Channel
        from src.services.websub_service import WebSubService

        settings = get_settings()
        if not settings.websub_enabled:
            logger.info(
                "Skipping WebSub subscribe for %s — PUBLIC_BASE_URL not set",
                channel_id,
            )
            return {"status": "skipped_no_public_url", "channel_id": channel_id}

        async with _get_db_session() as db:
            result = await db.execute(select(Channel).where(Channel.id == uuid.UUID(channel_id)))
            channel = result.scalar_one_or_none()
            if not channel:
                return {"status": "not_found", "channel_id": channel_id}

            if channel.websub_status == "disabled":
                return {"status": "disabled", "channel_id": channel_id}

            websub = WebSubService(settings)
            try:
                lease_expires = await websub.subscribe(channel.youtube_channel_id)
                channel.websub_subscribed_at = datetime.now(UTC)
                channel.websub_lease_expires_at = lease_expires
                # Status becomes active after hub verifies; mark active optimistically
                # once hub accepted the subscribe request (async verify).
                channel.websub_status = "active"
                await db.commit()
                return {
                    "status": "subscribed",
                    "channel_id": channel_id,
                    "lease_expires_at": lease_expires.isoformat(),
                }
            except Exception as e:
                logger.exception("WebSub subscribe failed for channel %s", channel_id)
                channel.websub_status = "failed"
                await db.commit()
                return {
                    "status": "failed",
                    "channel_id": channel_id,
                    "error": str(e),
                }

    return asyncio.run(_run_and_cleanup(_run()))


@celery_app.task(bind=True, name="pipeline.renew_websub_leases")
def renew_websub_leases_task(self) -> dict:
    """Renew WebSub subscriptions that are expiring, pending, or failed."""

    async def _run():
        from sqlalchemy import or_, select

        from src.config import get_settings
        from src.models.channel import Channel

        settings = get_settings()
        if not settings.websub_enabled:
            return {"status": "skipped_no_public_url", "renewed": 0}

        margin = timedelta(hours=settings.websub_renew_margin_hours)
        threshold = datetime.now(UTC) + margin

        async with _get_db_session() as db:
            result = await db.execute(
                select(Channel).where(
                    Channel.websub_status != "disabled",
                    or_(
                        Channel.websub_status.in_(("pending", "failed")),
                        Channel.websub_lease_expires_at.is_(None),
                        Channel.websub_lease_expires_at <= threshold,
                    ),
                )
            )
            channels = list(result.scalars().all())
            channel_ids = [str(c.id) for c in channels]

        for cid in channel_ids:
            subscribe_channel_websub_task.delay(cid)

        return {"status": "ok", "queued": len(channel_ids), "channel_ids": channel_ids}

    return asyncio.run(_run_and_cleanup(_run()))


@celery_app.task(bind=True, name="pipeline.poll_channels_for_new_videos")
def poll_channels_for_new_videos_task(self) -> dict:
    """RSS fallback: poll all channels' public feeds for unknown video IDs."""

    async def _run():
        services = _get_services()
        from sqlalchemy import select

        from src.models.channel import Channel
        from src.services.discovery_service import DiscoveryService
        from src.services.websub_service import WebSubService

        websub = WebSubService()
        enqueued = 0
        channels_checked = 0
        errors = 0

        async with _get_db_session() as db:
            result = await db.execute(select(Channel).where(Channel.websub_status != "disabled"))
            channels = list(result.scalars().all())

        for channel in channels:
            try:
                entries = await websub.fetch_rss_feed(channel.youtube_channel_id)
                # Tag entries with channel id in case feed omits yt:channelId
                tagged = []
                for e in entries:
                    tagged.append(
                        type(e)(
                            youtube_video_id=e.youtube_video_id,
                            youtube_channel_id=e.youtube_channel_id or channel.youtube_channel_id,
                            title=e.title,
                            published_at=e.published_at,
                        )
                    )

                async with _get_db_session() as db:
                    discovery = DiscoveryService(db, services["youtube"])
                    results = await discovery.handle_websub_entries(tagged, source="rss_fallback")
                    # Update last_checked even if nothing new
                    from sqlalchemy import select as sa_select

                    ch = (
                        await db.execute(sa_select(Channel).where(Channel.id == channel.id))
                    ).scalar_one()
                    ch.last_checked_at = datetime.now(UTC)
                    await db.commit()

                for r in results:
                    if r.get("enqueue") and r.get("video_id"):
                        auto_ingest_video_task.delay(r["video_id"])
                        enqueued += 1
                channels_checked += 1
            except Exception as e:
                errors += 1
                logger.warning(
                    "RSS fallback poll failed for %s: %s",
                    channel.youtube_channel_id,
                    e,
                )

        return {
            "status": "ok",
            "channels_checked": channels_checked,
            "enqueued": enqueued,
            "errors": errors,
        }

    return asyncio.run(_run_and_cleanup(_run()))


@celery_app.task(bind=True, name="pipeline.update_performance")
def update_performance_task(self) -> dict:
    """Periodic task: update performance metrics for all pending predictions."""

    async def _run():
        services = _get_services()
        async with _get_db_session() as db:
            from src.pipeline.market_tracking import MarketTrackingPipeline

            market = MarketTrackingPipeline(db, services["market_data"])
            result = await market.track_all_pending()
            await db.commit()
            return result

    return asyncio.run(_run_and_cleanup(_run()))


@celery_app.task(bind=True, name="pipeline.generate_embeddings")
def generate_embeddings_task(self) -> dict:
    """Generate embeddings for all segments that are missing them."""

    async def _run():
        services = _get_services()
        async with _get_db_session() as db:
            from src.pipeline.embeddings import EmbeddingPipeline

            embedding = EmbeddingPipeline(db, services["embedding"])
            result = await embedding.embed_all_pending()
            await db.commit()
            return result

    return asyncio.run(_run_and_cleanup(_run()))


# ── TickerFlow tasks ─────────────────────────────────────────────────────


@celery_app.task(bind=True, name="tickerflow.watchlist_collect")
def tickerflow_watchlist_collect_task(self) -> dict:
    """Collect social-sentiment data for all pilot watchlist symbols.

    Replaces the market-chatter async worker loop with a proper Celery
    periodic task.  Schedule via Beat (e.g. daily at 01:00 UTC).
    """

    async def _run():
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        from src.config import get_settings
        from src.database import engine
        from src.services.market_chatter.cache import JsonCache
        from src.services.market_chatter.collection_service import CollectionService
        from src.services.market_chatter.providers import (
            build_price_provider,
            build_sentiment_provider,
        )

        settings = get_settings()
        if not settings.enable_watchlist_worker:
            return {"status": "disabled", "symbols": []}

        symbols = settings.pilot_symbols
        if not symbols:
            return {"status": "no_symbols", "symbols": []}

        cache = await JsonCache.connect(settings.redis_url)
        sentiment_provider = build_sentiment_provider(settings)
        price_provider = build_price_provider(settings)

        session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        service = CollectionService(
            settings=settings,
            session_factory=session_factory,
            cache=cache,
            sentiment_provider=sentiment_provider,
            price_provider=price_provider,
        )

        results = {}
        for symbol in symbols:
            try:
                outcome = await service.collect(symbol)
                results[symbol] = {
                    "status": "ok",
                    "sources": len(outcome.snapshots),
                    "requests": outcome.request_count,
                }
            except Exception as e:
                logger.warning("Watchlist collect failed for %s: %s", symbol, e)
                results[symbol] = {"status": "error", "error": str(e)}

        await sentiment_provider.close()
        await cache.close()

        return {"status": "completed", "symbols": results}

    return asyncio.run(_run_and_cleanup(_run()))
