"""Pipeline trigger API endpoints."""

from fastapi import APIRouter

from src.schemas import (
    BackfillRequest,
    IngestSingleVideoRequest,
    PipelineStatusResponse,
    ProcessVideoRequest,
)
from src.tasks.pipeline_tasks import (
    backfill_channel_task,
    generate_embeddings_task,
    ingest_single_video_task,
    process_video_task,
    update_performance_task,
)

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])


@router.post("/process-video", response_model=PipelineStatusResponse)
async def trigger_process_video(request: ProcessVideoRequest) -> PipelineStatusResponse:
    """Trigger full processing pipeline for a single video.

    Queues a Celery task that runs: LLM analysis → theme mapping → embeddings → market tracking.
    """
    task = process_video_task.delay(str(request.video_id))
    return PipelineStatusResponse(task_id=task.id, status="queued")


@router.post("/ingest-single-video", response_model=PipelineStatusResponse)
async def trigger_ingest_single_video(
    request: IngestSingleVideoRequest,
) -> PipelineStatusResponse:
    """Ingest a single YouTube video for an existing channel and trigger its processing pipeline."""
    task = ingest_single_video_task.delay(str(request.channel_id), request.youtube_video_id)
    return PipelineStatusResponse(task_id=task.id, status="queued")


@router.post("/backfill", response_model=PipelineStatusResponse)
async def trigger_backfill(request: BackfillRequest) -> PipelineStatusResponse:
    """Trigger full backfill pipeline for a YouTube channel.

    Queues a Celery task that: ingests the channel -> fetches videos ->
    fetches transcripts -> queues processing for each video.
    """
    task = backfill_channel_task.delay(request.youtube_channel_id, request.max_videos)
    return PipelineStatusResponse(task_id=task.id, status="queued")


@router.post("/update-performance", response_model=PipelineStatusResponse)
async def trigger_performance_update() -> PipelineStatusResponse:
    """Trigger performance metric update for all pending predictions."""
    task = update_performance_task.delay()
    return PipelineStatusResponse(task_id=task.id, status="queued")


@router.post("/generate-embeddings", response_model=PipelineStatusResponse)
async def trigger_embedding_generation() -> PipelineStatusResponse:
    """Trigger embedding generation for all segments missing embeddings."""
    task = generate_embeddings_task.delay()
    return PipelineStatusResponse(task_id=task.id, status="queued")
