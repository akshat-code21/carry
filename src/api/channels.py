"""Channels API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_aggregation_service
from src.database import get_db
from src.models.channel import Channel
from src.schemas import ChannelResponse
from src.services.aggregation_service import AggregationService

router = APIRouter(prefix="/api/channels", tags=["Channels"])


@router.get("", response_model=list[ChannelResponse])
async def list_channels(
    db: AsyncSession = Depends(get_db),
) -> list[ChannelResponse]:
    """List all ingested channels."""
    result = await db.execute(select(Channel).order_by(Channel.created_at.desc()))
    channels = result.scalars().all()
    return [ChannelResponse.model_validate(c) for c in channels]


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ChannelResponse:
    """Get channel details."""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    return ChannelResponse.model_validate(channel)


@router.get("/{channel_id}/top-stocks")
async def get_channel_top_stocks(
    channel_id: UUID,
    limit: int = Query(default=20, ge=1, le=50),
    aggregation: AggregationService = Depends(get_aggregation_service),
) -> list[dict]:
    """Get top stocks for a channel ranked by relevance × mentions × sentiment."""
    return await aggregation.get_channel_top_stocks(channel_id, limit)
