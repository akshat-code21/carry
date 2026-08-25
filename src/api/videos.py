"""Videos API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.service import analytics
from src.api.deps import get_aggregation_service
from src.database import get_db
from src.models.prediction import Prediction
from src.models.theme import ThemeMention
from src.models.video import Video
from src.schemas import (
    PredictionResponse,
    ThemeMentionResponse,
    VideoDetailResponse,
    VideoResponse,
)
from src.services.aggregation_service import AggregationService

router = APIRouter(prefix="/api/videos", tags=["Videos"])


@router.get("", response_model=list[VideoResponse])
async def list_videos(
    channel_id: UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[VideoResponse]:
    """List processed videos, optionally filtered by channel. Excludes Shorts."""
    stmt = (
        select(Video)
        .where(Video.duration_sec > 60)
        .order_by(Video.published_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if channel_id:
        stmt = stmt.where(Video.channel_id == channel_id)

    result = await db.execute(stmt)
    videos = result.scalars().all()
    return [VideoResponse.model_validate(v) for v in videos]


@router.get("/{video_id}", response_model=VideoDetailResponse)
async def get_video(
    video_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> VideoDetailResponse:
    """Get video detail with predictions and theme mentions."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Fetch predictions
    pred_result = await db.execute(select(Prediction).where(Prediction.video_id == video_id))
    predictions = pred_result.scalars().all()

    # Fetch theme mentions
    mention_result = await db.execute(select(ThemeMention).where(ThemeMention.video_id == video_id))
    mentions = mention_result.scalars().all()

    response = VideoDetailResponse.model_validate(video)
    response.predictions = [PredictionResponse.model_validate(p) for p in predictions]
    response.theme_mentions = [ThemeMentionResponse.model_validate(m) for m in mentions]

    analytics.record_event(
        "video_viewed",
        payload={
            "video_id": str(video_id),
            "youtube_video_id": video.youtube_video_id,
            "prediction_count": len(predictions),
        },
        counters={"video_views": 1},
    )
    return response


@router.get("/{video_id}/stocks")
async def get_video_stocks(
    video_id: UUID,
    limit: int = Query(default=10, ge=1, le=50),
    aggregation: AggregationService = Depends(get_aggregation_service),
) -> list[dict]:
    """Get top stocks discussed in a video."""
    return await aggregation.get_video_top_stocks(video_id, limit)
