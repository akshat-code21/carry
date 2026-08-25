"""Investor CRUD service — adapted from Pet-Project for yt-chatter."""

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.content_item import ContentItem
from src.models.hfi_alert import HfiAlert
from src.models.hfi_report import HfiReport
from src.models.hfi_source import HfiSource
from src.models.investor import Investor

logger = structlog.get_logger()


async def list_investors(db: AsyncSession, user_id: uuid.UUID) -> list[Investor]:
    result = await db.execute(
        select(Investor).where(Investor.user_id == user_id).order_by(Investor.created_at.desc())
    )
    investors = result.scalars().all()
    # Attach sources_count
    for inv in investors:
        count_result = await db.execute(
            select(func.count()).select_from(HfiSource).where(HfiSource.investor_id == inv.id)
        )
        inv.sources_count = count_result.scalar_one()
    return investors


async def get_investor(
    db: AsyncSession, investor_id: uuid.UUID, user_id: uuid.UUID
) -> Investor | None:
    result = await db.execute(
        select(Investor)
        .options(selectinload(Investor.sources))
        .where(Investor.id == investor_id, Investor.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_investor(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    name: str,
    description: str | None = None,
    cik_number: str | None = None,
) -> Investor:
    investor = Investor(
        user_id=user_id,
        name=name,
        description=description,
        cik_number=_pad_cik(cik_number) if cik_number else None,
    )
    db.add(investor)
    await db.flush()

    if cik_number:
        from src.services.hfi.source_service import ensure_sec_13f_source

        await ensure_sec_13f_source(db, investor.id, investor.name, _pad_cik(cik_number))

    await db.refresh(investor)
    investor.sources_count = 0
    return investor


async def update_investor(
    db: AsyncSession, investor_id: uuid.UUID, user_id: uuid.UUID, **fields
) -> Investor | None:
    investor = await get_investor(db, investor_id, user_id)
    if not investor:
        return None
    for field, value in fields.items():
        if value is not None:
            setattr(investor, field, value)
    investor.updated_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(investor)

    if investor.cik_number:
        from src.services.hfi.source_service import ensure_sec_13f_source

        await ensure_sec_13f_source(db, investor.id, investor.name, investor.cik_number)

    return investor


async def delete_investor(db: AsyncSession, investor_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    investor = await get_investor(db, investor_id, user_id)
    if not investor:
        return False
    await db.delete(investor)
    return True


async def get_investor_stats(db: AsyncSession, investor_id: uuid.UUID) -> dict:
    content_count = (
        await db.execute(
            select(func.count())
            .select_from(ContentItem)
            .where(ContentItem.investor_id == investor_id)
        )
    ).scalar_one()
    report_count = (
        await db.execute(
            select(func.count()).select_from(HfiReport).where(HfiReport.investor_id == investor_id)
        )
    ).scalar_one()
    unread_alerts = (
        await db.execute(
            select(func.count())
            .select_from(HfiAlert)
            .where(
                HfiAlert.investor_id == investor_id,
                HfiAlert.is_read == False,  # noqa: E712
            )
        )
    ).scalar_one()
    return {"content_items": content_count, "reports": report_count, "unread_alerts": unread_alerts}


def _pad_cik(cik: str) -> str:
    return cik.zfill(10)
