"""Pipeline trigger API endpoints (admin-only — these enqueue expensive work)."""

from fastapi import APIRouter, Depends

from src.analytics.service import analytics
from src.auth.dependencies import require_admin
from src.models.user import User
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

router = APIRouter(
    prefix="/api/pipeline",
    tags=["Pipeline"],
    dependencies=[Depends(require_admin)],
)


@router.post("/process-video", response_model=PipelineStatusResponse)
async def trigger_process_video(
    request: ProcessVideoRequest,
    user: User = Depends(require_admin),
) -> PipelineStatusResponse:
    """Trigger full processing pipeline for a single video.

    Queues a Celery task that runs: LLM analysis → theme mapping → embeddings → market tracking.
    """
    task = process_video_task.delay(str(request.video_id))
    analytics.record_event(
        "pipeline_triggered",
        payload={"kind": "process_video", "video_id": str(request.video_id), "task_id": task.id},
        counters={"expensive_ops": 1},
    )
    return PipelineStatusResponse(task_id=task.id, status="queued")


@router.post("/ingest-single-video", response_model=PipelineStatusResponse)
async def trigger_ingest_single_video(
    request: IngestSingleVideoRequest,
    user: User = Depends(require_admin),
) -> PipelineStatusResponse:
    """Ingest a single YouTube video for an existing channel and trigger its processing pipeline."""
    task = ingest_single_video_task.delay(str(request.channel_id), request.youtube_video_id)
    analytics.record_event(
        "pipeline_triggered",
        payload={
            "kind": "ingest_single_video",
            "channel_id": str(request.channel_id),
            "youtube_video_id": request.youtube_video_id,
            "task_id": task.id,
        },
        counters={"expensive_ops": 1},
    )
    return PipelineStatusResponse(task_id=task.id, status="queued")


@router.post("/backfill", response_model=PipelineStatusResponse)
async def trigger_backfill(
    request: BackfillRequest,
    user: User = Depends(require_admin),
) -> PipelineStatusResponse:
    """Trigger full backfill pipeline for a YouTube channel.

    Queues a Celery task that: ingests the channel -> fetches videos ->
    fetches transcripts -> queues processing for each video.
    """
    task = backfill_channel_task.delay(request.youtube_channel_id, request.max_videos)
    analytics.record_event(
        "pipeline_triggered",
        payload={
            "kind": "backfill",
            "youtube_channel_id": request.youtube_channel_id,
            "max_videos": request.max_videos,
            "task_id": task.id,
        },
        counters={"expensive_ops": 1},
    )
    return PipelineStatusResponse(task_id=task.id, status="queued")


@router.post("/update-performance", response_model=PipelineStatusResponse)
async def trigger_performance_update(
    user: User = Depends(require_admin),
) -> PipelineStatusResponse:
    """Trigger performance metric update for all pending predictions."""
    task = update_performance_task.delay()
    analytics.record_event(
        "pipeline_triggered",
        payload={"kind": "update_performance", "task_id": task.id},
        counters={"expensive_ops": 1},
    )
    return PipelineStatusResponse(task_id=task.id, status="queued")


@router.post("/generate-embeddings", response_model=PipelineStatusResponse)
async def trigger_embedding_generation(
    user: User = Depends(require_admin),
) -> PipelineStatusResponse:
    """Trigger embedding generation for all segments missing embeddings."""
    task = generate_embeddings_task.delay()
    analytics.record_event(
        "pipeline_triggered",
        payload={"kind": "generate_embeddings", "task_id": task.id},
        counters={"expensive_ops": 1},
    )
    return PipelineStatusResponse(task_id=task.id, status="queued")
