"""Investor CRUD + sync endpoints."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.database import get_db
from src.models.content_item import ContentItem
from src.models.hfi_source import HfiSource
from src.models.user import User
from src.schemas.hfi import (
    ContentItemOut,
    InvestorCreate,
    InvestorOut,
    InvestorStats,
    InvestorUpdate,
    SourceCreate,
    SourceOut,
    SyncResponse,
)
from src.services.hfi import investor_service

router = APIRouter(prefix="/api/hfi/investors", tags=["HFI — Investors"])


@router.get("", response_model=list[InvestorOut])
async def list_investors(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await investor_service.list_investors(db, user.id)


@router.get("/{investor_id}", response_model=InvestorOut)
async def get_investor(
    investor_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    investor = await investor_service.get_investor(db, investor_id, user.id)
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    return investor


@router.post("", response_model=InvestorOut, status_code=201)
async def create_investor(
    body: InvestorCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await investor_service.create_investor(
        db,
        user.id,
        name=body.name,
        description=body.description,
        cik_number=body.cik_number,
    )


@router.patch("/{investor_id}", response_model=InvestorOut)
async def update_investor(
    investor_id: uuid.UUID,
    body: InvestorUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    investor = await investor_service.update_investor(
        db,
        investor_id,
        user.id,
        **body.model_dump(exclude_unset=True),
    )
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    return investor


@router.delete("/{investor_id}", status_code=204)
async def delete_investor(
    investor_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await investor_service.delete_investor(db, investor_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Investor not found")


@router.get("/{investor_id}/stats", response_model=InvestorStats)
async def get_investor_stats(
    investor_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    investor = await investor_service.get_investor(db, investor_id, user.id)
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    return await investor_service.get_investor_stats(db, investor_id)


@router.get("/{investor_id}/sources", response_model=list[SourceOut])
async def get_investor_sources(
    investor_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    investor = await investor_service.get_investor(db, investor_id, user.id)
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    result = await db.execute(
        select(HfiSource).where(HfiSource.investor_id == investor_id).order_by(HfiSource.created_at)
    )
    return list(result.scalars().all())


@router.post("/{investor_id}/sources", response_model=SourceOut, status_code=201)
async def create_investor_source(
    investor_id: uuid.UUID,
    body: SourceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    investor = await investor_service.get_investor(db, investor_id, user.id)
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    from src.services.hfi import source_service

    return await source_service.create_source(
        db,
        investor_id=investor_id,
        source_type=body.source_type,
        url=body.url,
        label=body.label,
        config=body.config,
    )


@router.delete("/sources/{source_id}", status_code=204)
async def delete_source(
    source_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from src.services.hfi import source_service

    deleted = await source_service.delete_source(db, source_id, user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")


@router.get("/{investor_id}/content", response_model=list[ContentItemOut])
async def get_investor_content(
    investor_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    investor = await investor_service.get_investor(db, investor_id, user.id)
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    result = await db.execute(
        select(ContentItem)
        .where(ContentItem.investor_id == investor_id)
        .order_by(ContentItem.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


@router.post("/{investor_id}/sync", response_model=SyncResponse)
async def sync_investor(
    investor_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger ingestion + processing for this investor. Runs in background."""
    investor = await investor_service.get_investor(db, investor_id, user.id)
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    from src.tasks.hfi_jobs import process_pending_content_for_investor, run_ingestion_for_investor

    async def _sync():
        await run_ingestion_for_investor(investor_id)
        await process_pending_content_for_investor(investor_id)

    background_tasks.add_task(_sync)

    return SyncResponse(
        investor_id=investor_id,
        status="queued",
    )
