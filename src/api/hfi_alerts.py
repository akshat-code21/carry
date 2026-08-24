"""HFI Alerts endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.database import get_db
from src.models.user import User
from src.schemas.hfi import AlertOut, AlertsResponse
from src.services.hfi import alert_service

router = APIRouter(prefix="/api/hfi/alerts", tags=["HFI — Alerts"])


@router.get("", response_model=AlertsResponse)
async def list_alerts(
    investor_id: uuid.UUID | None = Query(None),
    severity: str | None = Query(None),
    unread_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alerts, total, unread_count = await alert_service.list_alerts(
        db,
        user.id,
        investor_id=investor_id,
        severity=severity,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return AlertsResponse(
        alerts=[AlertOut.model_validate(a) for a in alerts],
        total=total,
        unread_count=unread_count,
    )


@router.post("/{alert_id}/read", response_model=AlertOut)
async def mark_alert_read(
    alert_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alert = await alert_service.mark_alert_read(db, alert_id, user.id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/read-all", status_code=200)
async def mark_all_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await alert_service.mark_all_read(db, user.id)
    return {"marked_read": count}
