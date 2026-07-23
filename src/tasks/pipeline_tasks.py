"""Celery tasks for the data pipeline.

Each task wraps a pipeline step and runs it asynchronously via Celery.
Tasks use asyncio.run() to bridge Celery's sync worker with async pipeline code.
"""

import asyncio
import logging
import uuid

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
            from src.pipeline.analysis import AnalysisPipeline
            from src.pipeline.embeddings import EmbeddingPipeline
            from src.pipeline.market_tracking import MarketTrackingPipeline
            from src.pipeline.theme_mapping import ThemeMappingPipeline
            from src.services.aggregation_service import AggregationService
            from src.services.theme_service import ThemeService

            vid = uuid.UUID(video_id)
            results = {}

            # Step 2: LLM Analysis
            theme_service = ThemeService(db)
            analysis = AnalysisPipeline(db, services["llm"], theme_service)
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

            await db.commit()
            return results

    return asyncio.run(_run_and_cleanup(_run()))


@celery_app.task(bind=True, name="pipeline.backfill_channel")
def backfill_channel_task(self, youtube_channel_id: str, max_videos: int = 20) -> dict:
    """Run full ingestion + processing pipeline for a channel.

    Steps: ingest channel → backfill videos → fetch transcripts → process each video
    """

    async def _run():
        services = _get_services()
        async with _get_db_session() as db:
            from src.pipeline.ingestion import IngestionPipeline

            # Step 1: Ingestion
            ingestion = IngestionPipeline(
                db, services["youtube"], services["transcript"]
            )
            ingestion_result = await ingestion.ingest_and_backfill(
                youtube_channel_id, max_videos
            )
            await db.commit()

        # Process each video as a separate task
        from sqlalchemy import select

        from src.models.video import Video

        async with _get_db_session() as db:
            result = await db.execute(
                select(Video).where(
                    Video.transcript_status == "fetched",
                    Video.processed.is_(False),
                )
            )
            unprocessed = result.scalars().all()
            video_ids = [str(v.id) for v in unprocessed]

        # Queue processing tasks for each video
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

            ingestion = IngestionPipeline(
                db, services["youtube"], services["transcript"]
            )
            c_uuid = uuid.UUID(channel_id)
            video = await ingestion.ingest_single_video(c_uuid, youtube_video_id)
            await db.commit()
            video_id_str = str(video.id)

        # Trigger single-video processing pipeline (LLM analysis, themes, market tracking)
        process_video_task.delay(video_id_str)

        return {
            "video_id": video_id_str,
            "youtube_video_id": youtube_video_id,
            "status": "queued_for_processing",
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
