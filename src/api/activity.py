"""In-app activity feed API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas import ActivityEventResponse, ActivityUnreadCountResponse
from src.services.activity_service import ActivityService

router = APIRouter(prefix="/api/activity", tags=["Activity"])


@router.get("", response_model=list[ActivityEventResponse])
async def list_activity(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> list[ActivityEventResponse]:
    """List recent activity events (newest first)."""
    service = ActivityService(db)
    events = await service.list_events(
        limit=limit, offset=offset, unread_only=unread_only
    )
    return [ActivityEventResponse.model_validate(e) for e in events]


@router.get("/unread-count", response_model=ActivityUnreadCountResponse)
async def unread_count(
    db: AsyncSession = Depends(get_db),
) -> ActivityUnreadCountResponse:
    """Return count of unread activity events for the topbar badge."""
    service = ActivityService(db)
    count = await service.unread_count()
    return ActivityUnreadCountResponse(count=count)


@router.post("/{event_id}/read", response_model=ActivityEventResponse)
async def mark_read(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ActivityEventResponse:
    """Mark a single activity event as read."""
    service = ActivityService(db)
    event = await service.mark_read(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Activity event not found")
    await db.commit()
    return ActivityEventResponse.model_validate(event)


@router.post("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark all activity events as read."""
    service = ActivityService(db)
    updated = await service.mark_all_read()
    await db.commit()
    return {"marked_read": updated}
