"""Channels API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func as sqlfunc
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.service import analytics
from src.api.deps import get_aggregation_service
from src.database import get_db
from src.models.channel import Channel
from src.models.video import Video
from src.schemas import ChannelResponse
from src.services.aggregation_service import AggregationService

router = APIRouter(prefix="/api/channels", tags=["Channels"])


@router.get("", response_model=list[ChannelResponse])
async def list_channels(
    db: AsyncSession = Depends(get_db),
) -> list[ChannelResponse]:
    """List all ingested channels with processed video counts."""
    video_counts_subq = (
        select(Video.channel_id, sqlfunc.count(Video.id).label("video_count"))
        .where(Video.duration_sec > 60)
        .group_by(Video.channel_id)
        .subquery()
    )
    stmt = (
        select(Channel, sqlfunc.coalesce(video_counts_subq.c.video_count, 0).label("video_count"))
        .outerjoin(video_counts_subq, Channel.id == video_counts_subq.c.channel_id)
        .order_by(Channel.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    channel_list = []
    for channel, count in rows:
        resp = ChannelResponse.model_validate(channel)
        resp.video_count = count
        channel_list.append(resp)
    return channel_list


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ChannelResponse:
    """Get channel details with processed video count."""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    video_count = await db.scalar(
        select(sqlfunc.count(Video.id)).where(
            Video.channel_id == channel_id, Video.duration_sec > 60
        )
    )

    analytics.record_event(
        "channel_viewed",
        payload={
            "channel_id": str(channel_id),
            "youtube_channel_id": channel.youtube_channel_id,
            "title": channel.title[:200],
        },
        counters={"channel_views": 1},
    )
    response = ChannelResponse.model_validate(channel)
    response.video_count = video_count or 0
    return response


@router.get("/{channel_id}/top-stocks")
async def get_channel_top_stocks(
    channel_id: UUID,
    limit: int = Query(default=20, ge=1, le=50),
    aggregation: AggregationService = Depends(get_aggregation_service),
) -> list[dict]:
    """Get top stocks for a channel ranked by relevance × mentions × sentiment."""
    return await aggregation.get_channel_top_stocks(channel_id, limit)
